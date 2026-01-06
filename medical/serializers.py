from rest_framework import serializers
from .models import Patient, Appointment, ToothFinding, TreatmentStep
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

class ToothFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToothFinding
        fields = ['id', 'tooth_number', 'condition', 'surface', 'notes', 'created_at']


class TreatmentStepSerializer(serializers.ModelSerializer):
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TreatmentStep
        fields = [
            'id', 'tooth_number', 'step_type', 'step_type_display', 
            'description', 'status', 'status_display', 'created_at', 'updated_at'
        ]

class PatientSerializer(serializers.ModelSerializer):
    # 1. Include the property from the Model
    full_name = serializers.ReadOnlyField() 
    
    # 2. Include the Tooth History (FDI logic)
    # 'toothfinding_set' is the default name Django gives to the reverse relationship
    findings = ToothFindingSerializer(many=True, read_only=True, source='toothfinding_set')

    class Meta:
        model = Patient
        # We list them explicitly to control the ORDER and ensure 
        # computed fields like 'full_name' are included.
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'full_name', 
            'cin', 
            'phone', 
            'insurance_type', 
            'insurance_id', 
            'findings', # This is your FDI history!
            'created_at'
        ]
    
    def create(self, validated_data):
        """Override create to ensure proper patient creation"""
        return Patient.objects.create(**validated_data)

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
            'tooth_number', 'treatment_steps'
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