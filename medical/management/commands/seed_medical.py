import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from clinics.models import Clinic
from medical.models import Patient, Appointment, ToothFinding

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds Atlas Clinic (clinic_atlas)'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- SEEDING ATLAS CLINIC ---")
        
        # 1. Get Clinic Reference
        atlas = Clinic.objects.get(schema_name='clinic_atlas')

        # 2. Create Staff (Shared Table)
        # Doctor
        dr, _ = User.objects.update_or_create(
            username='dr_alami',
            defaults={'email': 'alami@atlas.ma', 'role': 'DOCTOR', 'clinic_id': atlas.id, 'is_staff': True}
        )
        dr.set_password('password123')
        dr.save()

        # Assistants
        for name in ['ass_nadia', 'ass_hassan']:
            ass, _ = User.objects.update_or_create(
                username=name,
                defaults={'email': f'{name}@atlas.ma', 'role': 'ASSISTANT', 'clinic_id': atlas.id, 'is_staff': True}
            )
            ass.set_password('password123')
            ass.save()

        # 3. Create Patients (Tenant Table - Auto-encrypted by your model)
        patients_data = [
            {"first": "Ahmed", "last": "Bennani", "cin": "AB123456", "phone": "0661223344"},
            {"first": "Sanaa", "last": "Alami", "cin": "GH901234", "phone": "0664556677"},
        ]
        
        patients = []
        for data in patients_data:
            p, _ = Patient.objects.update_or_create(
                cin=data['cin'],
                defaults={'first_name': data['first'], 'last_name': data['last'], 'phone': data['phone']}
            )
            patients.append(p)

        # 4. Create FDI History
        for p in patients:
            ToothFinding.objects.get_or_create(
                patient=p, tooth_number=24, 
                defaults={'condition': 'Caries', 'notes': 'A surveiller'}
            )

        # 5. Create Appointments
        now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        Appointment.objects.update_or_create(
            Subject="Consultation Ahmed",
            StartTime=now,
            defaults={
                'EndTime': now + timedelta(hours=1),
                'patient': patients[0],
                'doctor': dr,
                'CategoryColor': '#422afb',
                'tooth_number': 24
            }
        )

        self.stdout.write(self.style.SUCCESS("✅ Atlas Clinic Seeded Successfully"))