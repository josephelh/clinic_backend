import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection
from django_tenants.utils import tenant_context
from clinics.models import Clinic
from medical.models import Patient, Appointment

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds Al Mansour Clinic (clinic_mansour)'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- SEEDING AL MANSOUR CLINIC ---")
        
        # 1. Get Clinic Reference
        mansour = Clinic.objects.get(schema_name='clinic_mansour')
        
        # 2. Switch to tenant context
        with tenant_context(mansour):
            # 2. Create 2 Doctors
            doctors = []
            for name in ['dr_benjelloun', 'dr_chraibi']:
                doc, _ = User.objects.update_or_create(
                    username=name,
                    defaults={'email': f'{name}@mansour.ma', 'role': 'DOCTOR', 'clinic_id': mansour.id, 'is_staff': True}
                )
                doc.set_password('password123')
                doc.save()
                doctors.append(doc)

            # 3. Create 2 Assistants
            for name in ['ass_sara', 'ass_mehdi']:
                ass, _ = User.objects.update_or_create(
                    username=name,
                    defaults={'email': f'{name}@mansour.ma', 'role': 'ASSISTANT', 'clinic_id': mansour.id, 'is_staff': True}
                )
                ass.set_password('password123')
                ass.save()

            # 4. Create 20 Patients
            patients = []
            for i in range(20):
                p, _ = Patient.objects.update_or_create(
                    cin=f"MA999{i:02d}",
                    defaults={'first_name': f"Patient{i}", 'last_name': "Mansour", 'phone': f"0700000{i:02d}"}
                )
                patients.append(p)

            # 5. Create 30-40 Appointments spread across a week
            now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
            colors = ['#01b574', '#ffb547', '#ff6b6b', '#4ecdc4', '#45b7d1']
            
            appointment_count = 0
            for day_offset in range(7):  # 7 days
                current_date = now + timedelta(days=day_offset)
                # 5-6 appointments per day
                appointments_per_day = random.randint(5, 6)
                
                for time_slot in range(appointments_per_day):
                    appointment_time = current_date + timedelta(hours=time_slot)
                    
                    Appointment.objects.create(
                        Subject=f"Soin dentaire",
                        StartTime=appointment_time,
                        EndTime=appointment_time + timedelta(hours=1),
                        patient=random.choice(patients),
                        doctor=random.choice(doctors),
                        CategoryColor=random.choice(colors)
                    )
                    appointment_count += 1

            self.stdout.write(f"✅ Created {appointment_count} appointments")

        self.stdout.write(self.style.SUCCESS("✅ Al Mansour Clinic Seeded Successfully"))