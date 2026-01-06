from django.db import models

# Create your models here.
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Clinic(TenantMixin):
    name = models.CharField(max_length=100)
    plan_tier = models.IntegerField(default=1) # 1: Basic, 2: Pro, 3: Premium
    created_on = models.DateField(auto_now_add=True)

    # This allows django-tenants to automatically create the Postgres Schema
    auto_create_schema = True

class Domain(DomainMixin):
    pass