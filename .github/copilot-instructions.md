# AI Copilot Instructions for Clinc Dental Backend


AI Copilot Instructions: Django Multi-Tenant Backend (The Surgery)
1. Architecture & Schema Infrastructure

This system uses django-tenants for strict schema-based isolation.

The Two-Layer Map

Public Schema: Shared registry. Contains clinics.Clinic, clinics.Domain, and the shared users.User table.

Tenant Schemas: Private clinic data. Each clinic (e.g., clinic_atlas) gets its own isolated Postgres schema containing medical (EMR), billing, and inventory data.

Multi-Tenant Handshake (Identification Logic)

Middleware: django_tenants.middleware.main.TenantMainMiddleware MUST be the first entry in MIDDLEWARE.

Domain Matching: The system matches the Host header to the Domain table.

Port Handling: REMOVE_PORT_FROM_DOMAIN = True is required in settings.py for local dev (atlas.localhost:8000 → atlas.localhost).

Dynamic Routing:

urls_public.py: Handles POST /api/auth/login/ and super-admin.

urls_tenant.py: Handles the clinical API (/api/medical/, /api/auth/users/). Never include urls_public here to avoid circular dependencies.

App	Purpose	Schema	Key Models
clinics	Registry & Subdomain Management	Public	Clinic, Domain
users	Shared User Model & Auth	Public	User (DOCTOR/ASSISTANT/ADMIN)
medical	Patient EMR & FDI Logic	Tenant	Patient, Appointment, ToothFinding, TreatmentStep
billing	Moroccan NGAP & Invoicing	Tenant	Invoice, NGAPCode, Payment
2. Advanced Security & Privacy (Moroccan Law 09-08)
Data Encryption (Fernet)

Sensitive Fields: cin, phone, insurance_id, address MUST use EncryptedCharField.

Non-Deterministic rule: Fernet produces unique strings for identical inputs. Never use unique=True on encrypted fields.

Searchable Hashing Strategy (Deterministic)

For every encrypted field used for search/uniqueness (e.g., cin), use a twin field (e.g., cin_hash).

Implementation: In Patient.save(), use hashlib.sha256(value.strip().encode()).hexdigest().

Optional fields: If the source is empty, set hash to None to allow multiple NULLs in Postgres unique constraints.

The Login Guard (Cross-Tenant Security)

In CustomTokenObtainPairSerializer, verify user.clinic_id == connection.tenant.id.

Throw PermissionDenied if a user attempts to log into a clinic subdomain they are not assigned to.

3. Clinical Domain Logic (The Dental Standard)
FDI Dental Notation

Strict Standard: Use the FDI two-digit system (11-48). Never use alphabetic systems.

Storage: Always use models.IntegerField for tooth_number to enable range queries (e.g., 11 to 18).

Clinical EMR Workflow

Appointment: A time-slot container. Does NOT store tooth_number.

ToothFinding: Clinical state discovery (e.g., "Caries on 24"). Linked to Patient and optionally an Appointment.

TreatmentStep: The "Action" (e.g., "Extraction of 24"). Linked to an Appointment. Stores the tooth_number.

Prescription: Linked to an Appointment. Stores medications/dosage.

4. Feature Roadmap & AI Integration (Gemini 1.5 Flash)
AI Privacy Protocol

Anonymization: Before sending data to Gemini (CIN Scanner, Treatment Explainer), ViewSets MUST strip PII (Names, CIN). Use UUIDs or patient_id only.

SaaS Tier Gating

Tier 1 (Starter): 1 Doctor only, standard Agenda, standard EMR.

Tier 2 (Pro): Multiple Doctors (Resource Grouping), WhatsApp Automations, AI CIN Scanner.

Tier 3 (Enterprise): Inventory Tracking, AI Stock Forecasting, NGAP Billing Assistant.

5. Serializer & API Standards (Syncfusion Compatible)
Syncfusion Property Mapping

Syncfusion EJ2 is case-sensitive. Agenda Serializers must map fields exactly:

Id (from id)

Subject (from patient.full_name)

StartTime / EndTime (ISO 8601 Strings)

CategoryColor (Hex string)

Role-Based Access Control (RBAC)

ASSISTANT: Sees all appointments/patients in the current schema (queryset = all()).

DOCTOR: Sees all patients but only their own appointments (queryset = filter(doctor=request.user)).

6. Developer Workflows (Neon Cloud & Windows)
Common Commands (Active venv)
code
Powershell
download
content_copy
expand_less
# Migrations
python manage.py makemigrations
python manage.py migrate_schemas --schema=public
python manage.py migrate_schemas  # Applies to all clinics in Neon

# Database Seeding
python manage.py tenant_command seed_medical --schema=clinic_atlas
python manage.py tenant_command seed_mansour --schema=clinic_mansour

# Tenant Debugging
# Use 'connection.tenant.schema_name' to verify current context in shells/views
7. Prohibited Anti-Patterns

NO storage of PII (CIN/Phone) in plain-text.

NO Appointment.tooth_number. (Keep data normalized in TreatmentStep).

NO standard migrate. (Always use migrate_schemas).

NO hardcoded localhost:8000. (Use request.get_host()).

NO circular includes in urls_tenant.py (Do not include urls_public).

Task Context: You are currently helping develop the Patient EMR and FDI Tooth History module. Ensure all ViewSets filter by connection.tenant and all PII is encrypted.