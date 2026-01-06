# AI Copilot Instructions for Clinc Dental Backend

## Architecture Overview

This is a **Django-based multi-tenant dental clinic management system** using `django-tenants` for schema isolation.

### Critical Concepts

**Multi-Tenant Architecture:**
- **Public Schema**: Shared across all clinics (authentication, clinic registry, users list)
- **Tenant Schemas**: Each clinic gets its own isolated PostgreSQL schema containing medical records, appointments, and billing data
- Routing happens via domain/subdomain: `clinic1.localhost:8000` → clinic1's schema, `clinic2.localhost:8000` → clinic2's schema
- See [core/settings.py](core/settings.py#L32-L33) for tenant model configuration

**Database Isolation:**
- `clinics.Clinic` (TenantMixin) = tenant model; automatically creates schema on save
- `clinics.Domain` (DomainMixin) = maps domain names to clinics
- `users.User` (extends AbstractUser) = resides in public schema with `clinic_id` for easier reference
- Medical/billing data in tenant schemas via `medical.models`, `billing.models`

### Component Map

| App | Purpose | Schema | Key Files |
|-----|---------|--------|-----------|
| `clinics` | Clinic registry, domain management | Public | [models.py](clinics/models.py), [admin.py](clinics/admin.py) |
| `users` | Auth, user roles (DOCTOR/ASSISTANT/ADMIN) | Public | [models.py](users/models.py), [serializers.py](users/serializers.py) |
| `medical` | Patients, appointments, dental findings, tooth conditions | Tenant | [models.py](medical/models.py), [serializers.py](medical/serializers.py) |
| `billing` | Invoices, payments (skeleton) | Tenant | [models.py](billing/models.py) |

## Critical Patterns

### 1. Authentication & Authorization

**Custom Token Serializer** ([users/serializers.py](users/serializers.py#L15)):
- Validates user belongs to requested clinic via `clinic_id` match
- Blocks cross-tenant access with security check: `user.clinic_id != current_tenant.id` → `PermissionDenied`
- Includes `role`, `clinic_id` in token response
- Test with login on wrong domain to verify isolation works

**Login Flow:**
- Public URL: `POST /api/auth/login/` (routes to public schema)
- Tenant URL: `POST /api/auth/login/` (routes to tenant schema, validates clinic_id)
- Both URLs exist in [urls_public.py](core/urls_public.py#L10) and [urls_tenant.py](core/urls_tenant.py#L13)

### 2. Multi-Tenant Routing

**Middleware Chain** ([core/debug_middleware.py](core/debug_middleware.py)):
1. `TenantMainMiddleware` (django-tenants) inspects `request.get_host()` 
2. Looks up domain in `Domain` table
3. Sets `connection.tenant` to the matching `Clinic` object
4. Subsequent queries use tenant's schema

**Important:** Always reference `connection.tenant` in views to access current clinic info (see [users/serializers.py](users/serializers.py#L24)).

### 3. Data Models & Encryption

**Patient Model** ([medical/models.py](medical/models.py#L16)):
- Uses custom `EncryptedCharField` for CIN (ID number) using Fernet encryption
- Encryption key derived from Django SECRET_KEY
- Must handle decryption failures gracefully (catches exception, returns raw value)

**Tooth Finding System** (FDI Notation):
- `Appointment.tooth_number` = tooth position (FDI standard: 11-18, 21-28, etc.)
- `ToothFinding` tracks conditions per tooth (cavity, filling, root canal)
- Reverse relation: `Patient.toothfinding_set` auto-mapped as `findings` in serializer

**Appointment Model:**
- Links Patient → Doctor (User) → Tooth number
- Status codes: 'Scheduled', etc. (extensible)
- Uses `CategoryColor` for UI calendar rendering

### 4. Serializer Patterns

**Read-Only Properties** ([medical/serializers.py](medical/serializers.py#L13)):
- `full_name = serializers.ReadOnlyField()` pulls computed property from model
- Use `source='related_model.property'` for nested field access
- Example: `doctor_name` from `Doctor.username` via ForeignKey

**Nested Serializers** ([medical/serializers.py](medical/serializers.py#L18)):
- Use `source='reverse_relation_name'` to include related objects
- Django auto-names reverse relations: `Patient.toothfinding_set` → `source='toothfinding_set'`
- Set `read_only=True, many=True` for collections

### 5. Settings & Middleware

**App Lists** ([core/settings.py](core/settings.py#L42-L57)):
- `SHARED_APPS`: Always loaded (tenants, users, auth framework)
- `TENANT_APPS`: Loaded per schema (medical, billing)
- `INSTALLED_APPS`: Union of both

**URL Routing** ([core/settings.py](core/settings.py#L76-L77)):
- `PUBLIC_SCHEMA_URLCONF = 'core.urls_public'`
- `TENANT_URLCONF = 'core.urls_tenant'`
- Tenant users hit tenant URLs which include `medical.urls`

## Developer Workflows

### Running the Backend

```bash
# Start PostgreSQL via Docker
docker-compose up -d

# Apply migrations to public schema
python manage.py migrate --shared

# Apply migrations to all tenant schemas
python manage.py migrate

# Create development data (seeding)
python manage.py seed_medical
python manage.py seed_mansour

# Run server (default: http://localhost:8000 → public schema)
python manage.py runserver
```

### Testing Multi-Tenant Behavior

**Via Hosts File** (Windows):
```
127.0.0.1 clinic1.localhost
127.0.0.1 clinic2.localhost
```
Then visit `http://clinic1.localhost:8000/api/...` to test tenant routing.

**Via Port Forwarding** (without hosts file):
- Public: `http://localhost:8000`
- Tenant: `http://localhost:8001` (requires additional configuration)

### Debugging Tenant Context

- Check [core/debug_middleware.py](core/debug_middleware.py) output for tenant identification
- Console prints: schema name, clinic ID, domain found status
- Use `from django.db import connection; print(connection.tenant.schema_name)` in views

### Common Commands

```bash
# Create new tenant programmatically
python manage.py shell
>>> from clinics.models import Clinic, Domain
>>> clinic = Clinic.objects.create(name="New Clinic", schema_name="clinic_new")
>>> Domain.objects.create(domain="clinic-new.localhost", tenant=clinic)

# Run tests
python manage.py test

# Create superuser (in public schema)
python manage.py createsuperuser
```

## Key Files by Purpose

| Purpose | File |
|---------|------|
| Database schema separation | [core/settings.py](core/settings.py#L32-L33), [clinics/models.py](clinics/models.py) |
| Auth & role validation | [users/models.py](users/models.py), [users/serializers.py](users/serializers.py) |
| Tenant routing logic | [core/debug_middleware.py](core/debug_middleware.py) |
| API endpoints | [core/urls_tenant.py](core/urls_tenant.py), [medical/urls.py](medical/urls.py) |
| Data encryption | [medical/models.py](medical/models.py#L5-L16) |
| Appointment/tooth tracking | [medical/models.py](medical/models.py#L64-L79) |

## Gotchas & Anti-Patterns

1. **Don't forget clinic_id validation** → Always check `user.clinic_id == current_tenant.id` before returning sensitive data
2. **Encryption key management** → Currently uses SECRET_KEY; move to `.env` in production
3. **Cross-tenant queries impossible** → Cannot query `medical.models` from public schema; must route through tenant
4. **Domain creation required** → Just creating a Clinic doesn't activate it; must create a Domain entry first
5. **Shared vs tenant apps** → If model needs clinic isolation, put in `TENANT_APPS`; if shared across clinics, put in `SHARED_APPS`

## Questions to Ask When Adding Features

- **Is this clinic-specific data?** → Medical, billing, appointments = yes (tenant); clinics registry = no (public)
- **Does this need encryption?** → Sensitive patient data (CIN, phone) = yes; see `EncryptedCharField` implementation
- **Who can access this role?** → Define in [users/models.py](users/models.py#L5-L8) role choices; validate in views
- **Cross-tenant visibility needed?** → If no, schema isolation handles it automatically; if yes, surface explicitly in public schema
