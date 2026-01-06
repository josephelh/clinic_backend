from django_tenants.utils import get_tenant_domain_model

class TenantDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.db import connection
        from django.conf import settings
        
        # If TenantMainMiddleware didn't set the tenant, let's try to help
        if not hasattr(request, 'tenant') or request.tenant.schema_name == 'public':
            hostname = request.get_host().split(':')[0]
            from clinics.models import Domain
            try:
                domain = Domain.objects.select_related('tenant').get(domain=hostname)
                request.tenant = domain.tenant
                connection.set_tenant(request.tenant)
            except Domain.DoesNotExist:
                pass

        # Ensure URLConf is set for tenants
        if hasattr(request, 'tenant') and request.tenant.schema_name != 'public':
            request.urlconf = settings.TENANT_URLCONF
            
        response = self.get_response(request)
        return response