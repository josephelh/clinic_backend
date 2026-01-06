from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Clinic, Domain

class DomainInline(admin.TabularInline):
    model = Domain
    max_num = 1

@admin.register(Clinic)
class ClinicAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'plan_tier', 'created_on')
    inlines = [DomainInline]