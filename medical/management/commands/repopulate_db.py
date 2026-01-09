import random
from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from django_tenants.utils import tenant_context
from clinics.models import Clinic, Domain
from medical.models import Patient, Appointment, ToothFinding, TreatmentStep, Prescription

User = get_user_model()

class Command(BaseCommand):
    help = 'Fully resets database with conflict-free appointments on single days.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("!!! WIPING DATABASE (CLEAN SLATE) !!!"))

        # 1. Delete All Clinics (drops schemas)
        Clinic.objects.all().delete()
        self.stdout.write("Deleted all clinics and dropped schemas.")

        # 2. Cleanup Zombie Schemas & Public Pollution
        with connection.cursor() as cursor:
            # Check for zombie schemas
            cursor.execute("SELECT schema_name FROM information_schema.schemata")
            schemas = [r[0] for r in cursor.fetchall()]
            
            # Identify schemas with medical_appointment table
            cursor.execute("""
                SELECT table_schema 
                FROM information_schema.tables 
                WHERE table_name = 'medical_appointment'
            """)
            rogue_schemas = [r[0] for r in cursor.fetchall()]
            
            for schema in rogue_schemas:
                if schema != 'public':
                    self.stdout.write(f"Dropping zombie schema: {schema}")
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            
            # Clean public schema pollution
            cursor.execute("SET search_path TO public;")
            cursor.execute("""
                DROP TABLE IF EXISTS medical_treatmentstep CASCADE;
                DROP TABLE IF EXISTS medical_toothfinding CASCADE;
                DROP TABLE IF EXISTS medical_prescription CASCADE;
                DROP TABLE IF EXISTS medical_appointment CASCADE;
                DROP TABLE IF EXISTS medical_patient CASCADE;
                DROP TABLE IF EXISTS billing_invoice CASCADE;
                DROP TABLE IF EXISTS billing_payment CASCADE;
            """)
        
        # 3. Delete Users (Except Admin)
        with connection.cursor() as cursor:
             cursor.execute("DELETE FROM users_user WHERE username != 'admin'")
        self.stdout.write("Deleted all users (except 'admin').")

        # 4. Create Clinics
        self.stdout.write("--- CREATING CLINICS ---")
        
        # Atlas (Tier 1)
        atlas = Clinic.objects.create(
            name="Atlas Dental Center",
            schema_name="clinic_atlas",
            plan_tier=1
        )
        Domain.objects.create(domain="atlas.localhost", tenant=atlas, is_primary=True)

        # Mansour (Tier 3)
        mansour = Clinic.objects.create(
            name="Mansour Medical Group",
            schema_name="clinic_mansour",
            plan_tier=3
        )
        Domain.objects.create(domain="mansour.localhost", tenant=mansour, is_primary=True)

        # 5. Populate Data
        # Atlas: 1 Doc, 1 Asst
        self.populate_clinic(atlas, "Atlas", num_doctors=1, num_assistants=1, num_patients=10)
        
        # Mansour: 2 Docs, 2 Assts
        self.populate_clinic(mansour, "Mansour", num_doctors=2, num_assistants=2, num_patients=20)

        self.stdout.write(self.style.SUCCESS("✅ DATABASE REPOPULATED SUCCESSFULLY (NO CONFLICTS)"))

    def populate_clinic(self, clinic, name, num_doctors=1, num_assistants=1, num_patients=10):
        self.stdout.write(f"--- Populating {name} ---")

        doctors = []
        # Create Doctors
        for i in range(1, num_doctors + 1):
            if i == 1:
                u_name = f'dr_{name.lower()}'
                l_name = 'Doctor'
            else:
                u_name = f'dr_{name.lower()}_{i}'
                l_name = f'Doctor {i}'

            dr = User.objects.create_user(
                username=u_name,
                email=f'{u_name}@{name.lower()}.ma',
                password='password123',
                role='DOCTOR',
                clinic_id=clinic.id,
                first_name=f'Dr. {name}',
                last_name=l_name
            )
            doctors.append(dr)

        # Create Assistants
        for i in range(1, num_assistants + 1):
            u_name = f'asst_{name.lower()}' if i == 1 else f'asst_{name.lower()}_{i}'
            User.objects.create_user(
                username=u_name,
                email=f'{u_name}@{name.lower()}.ma',
                password='password123',
                role='ASSISTANT',
                clinic_id=clinic.id,
                first_name='Samira',
                last_name=f'Assistant {i}'
            )

        with tenant_context(clinic):
            # Create Patients
            patients = []
            for i in range(1, num_patients + 1):
                p = Patient(
                    first_name=f"Patient{i}",
                    last_name=f"{name}",
                    gender=random.choice(['M', 'F']),
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(7000, 20000)),
                    cin=f"{name[0].upper()}{i}000",
                    phone=f"060000000{i}",
                    insurance_type=random.choice(['AMO', 'MUTUELLE', 'NONE']),
                    insurance_id=f"INS-{i}-{random.randint(1000,9999)}" if i % 2 == 0 else None
                )
                p.save()
                patients.append(p)

            # Create Conflict-Free Appointments
            # Range: Last 30 days to next 14 days
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date() + timedelta(days=14)
            
            current_day = start_date
            while current_day <= end_date:
                # Skip Sundays
                if current_day.weekday() == 6:
                    current_day += timedelta(days=1)
                    continue

                for doc in doctors:
                    # 70% chance doctor works this day
                    if random.random() > 0.3:
                        self.create_daily_schedule(doc, current_day, patients)
                
                current_day += timedelta(days=1)

    def create_daily_schedule(self, doctor, date_obj, patients):
        # working hours 9:00 to 17:00
        start_hour = 9
        end_hour = 17
        
        # Start pointer
        current_time = datetime.combine(date_obj, time(start_hour, 0))
        # Ensure timezone awareness if settings.USE_TZ is True (it usually is in Django)
        current_time = timezone.make_aware(current_time)
        
        limit_time = datetime.combine(date_obj, time(end_hour, 0))
        limit_time = timezone.make_aware(limit_time)

        while current_time < limit_time:
            # 60% chance to book a slot, otherwise it's free time/break
            if random.random() > 0.4:
                # Pick random patient
                patient = random.choice(patients)
                
                # Duration: 30 or 60 mins
                duration_minutes = random.choice([30, 45, 60])
                
                start_dt = current_time
                end_dt = start_dt + timedelta(minutes=duration_minutes)

                # Check if we exceed work day limit
                if end_dt > limit_time:
                    break

                # Determine Status based on date
                now = timezone.now()
                if end_dt < now:
                    status = 'Completed'
                    color = '#1aaa55' # Green
                else:
                    status = 'Scheduled'
                    color = '#0077BE' # Blue

                # Create Appointment
                appt = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    Subject=f"Consultation {patient.first_name}",
                    StartTime=start_dt,
                    EndTime=end_dt,
                    Status=status,
                    CategoryColor=color
                )

                # If completed, add medical data
                if status == 'Completed':
                    self.add_medical_history(appt)

                # Move pointer: End time + 10 min break
                current_time = end_dt + timedelta(minutes=10)
            else:
                # Gap / No appointment
                current_time += timedelta(minutes=30)

    def add_medical_history(self, appointment):
        # Findings
        if random.random() > 0.5:
            ToothFinding.objects.create(
                patient=appointment.patient,
                tooth_number=random.randint(11, 48),
                condition='CARIES',
                found_in=appointment
            )

        # Treatment
        TreatmentStep.objects.create(
            appointment=appointment,
            tooth_number=random.randint(11, 48),
            step_type='cleaning',
            description="Routine cleaning",
            status='completed',
            price=random.randint(300, 800)
        )
