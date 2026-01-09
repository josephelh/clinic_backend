import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django_tenants.utils import tenant_context
from clinics.models import Clinic

def check_tables():
    clinics = Clinic.objects.exclude(schema_name='public')
    for clinic in clinics:
        print(f"--- Checking {clinic.schema_name} ---")
        with tenant_context(clinic):
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, [clinic.schema_name])
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"medical_appointment: {'✅' if 'medical_appointment' in tables else '❌'}")
                print(f"medical_treatmentstep: {'✅' if 'medical_treatmentstep' in tables else '❌'}")

if __name__ == '__main__':
    check_tables()
