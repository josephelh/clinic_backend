import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def check_public():
    print("--- Checking public ---")
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"medical_appointment in public: {'✅' if 'medical_appointment' in tables else '❌'}")
        print(f"medical_treatmentstep in public: {'✅' if 'medical_treatmentstep' in tables else '❌'}")

if __name__ == '__main__':
    check_public()
