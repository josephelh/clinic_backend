from django.core.management.base import BaseCommand
from clinics.models import Clinic, Domain

class Command(BaseCommand):
    help = 'Setup localhost domain for development'

    def handle(self, *args, **kwargs):
        # Get or create the public/SaaS clinic
        saas_clinic, created = Clinic.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'DentalConnect SaaS',
                'auto_create_schema': False,  # Public schema already exists
            }
        )

        # Create localhost domain pointing to the SaaS clinic
        domain, created = Domain.objects.get_or_create(
            domain='localhost',
            defaults={'tenant': saas_clinic}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created domain "localhost" pointing to {saas_clinic.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Domain "localhost" already exists'))

        # Also add 127.0.0.1 for direct IP access
        domain_ip, created = Domain.objects.get_or_create(
            domain='127.0.0.1',
            defaults={'tenant': saas_clinic}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created domain "127.0.0.1" pointing to {saas_clinic.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Domain "127.0.0.1" already exists'))
