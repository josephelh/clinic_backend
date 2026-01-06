from django.contrib import admin
from .models import Patient, Appointment, ToothFinding, TreatmentStep

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('Subject', 'patient', 'StartTime', 'Status')

@admin.register(ToothFinding)
class ToothFindingAdmin(admin.ModelAdmin):
    list_display = ('patient', 'tooth_number', 'condition')

@admin.register(TreatmentStep)
class TreatmentStepAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'tooth_number', 'step_type', 'status', 'created_at')
    list_filter = ('step_type', 'status', 'created_at')
    search_fields = ('appointment__Subject', 'tooth_number')
    readonly_fields = ('created_at', 'updated_at')