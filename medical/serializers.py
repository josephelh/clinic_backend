from rest_framework import serializers
from .models import Patient, Appointment, ToothFinding, TreatmentStep, Prescription
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

class ToothFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToothFinding
        fields = ['id', 'patient', 'tooth_number', 'condition', 'surface', 'notes', 'found_in', 'created_at']


class TreatmentStepSerializer(serializers.ModelSerializer):
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TreatmentStep
        fields = [
            'id', 'appointment', 'tooth_number', 'step_type', 'step_type_display', 
            'description', 'price', 'status', 'status_display', 'created_at', 'updated_at'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'patient', 'appointment', 'medications', 'notes', 'created_at']

# serializers.py

class PatientListSerializer(serializers.ModelSerializer):
    """
    Used ONLY for the Patient List table. 
    Excludes findings, alerts, and heavy medical history.
    """
    class Meta:
        model = Patient
        fields = [
            'id', 
            'first_name', 
            'last_name',
            'full_name', 
            'gender', 
            'date_of_birth', 
            'is_high_risk', 
            'phone' # For O(1) search in frontend if needed
        ]

class PatientDetailSerializer(serializers.ModelSerializer):
    """
    Used ONLY for the EMR Hub. Includes everything.
    """
    findings = ToothFindingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__' # Or specify all heavy fields
        


class AppointmentSerializer(serializers.ModelSerializer):
    # We pull these from the related Patient model
    patient_name = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    # Include treatment steps for this appointment
    treatment_steps = TreatmentStepSerializer(many=True, read_only=True)
    
    # We filter the doctor choices to only show doctors from the current clinic
    doctor = serializers.PrimaryKeyRelatedField(queryset=User.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            if 'request' in self.context:
                current_tenant = connection.tenant
                if current_tenant and current_tenant.schema_name != 'public':
                    # Filter doctors to current clinic
                    self.fields['doctor'].queryset = User.objects.filter(
                        clinic_id=current_tenant.id, 
                        role='DOCTOR'
                    )
                else:
                    # Fallback: get all doctors if tenant context not available
                    self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
        except Exception as e:
            # If tenant context fails, allow all doctors
            self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')

    class Meta:
        model = Appointment
        fields = [
            'id', 'Subject', 'StartTime', 'EndTime', 
            'Description', 'Status', 'CategoryColor',
            'patient', 'patient_name', 'patient_phone','doctor_name', 'doctor',
            'treatment_steps'
        ]

    def get_patient_name(self, obj):
        try:
            return obj.patient.full_name if obj.patient else None
        except Exception as e:
            return None

    def get_patient_phone(self, obj):
        try:
            return obj.patient.phone if obj.patient else None
        except Exception as e:
            return None
    
    def get_doctor_name(self, obj):
        try:
            return obj.doctor.username if obj.doctor else None
        except Exception as e:
            return None