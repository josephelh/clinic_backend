from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import PermissionDenied
from .models import User
from django.db import connection



class UserSerializer(serializers.ModelSerializer):
    # Property from model to help the UI
    full_name = serializers.ReadOnlyField() 

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'role']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 1. Standard authentication
        data = super().validate(attrs)

        # 2. SECURITY LOGIC
        current_tenant = connection.tenant
        
        # We only allow login if the user belongs to the current tenant
        if self.user.clinic_id != current_tenant.id:
            print(f"SECURITY BREACH BLOCKED: User {self.user.username} (Clinic {self.user.clinic_id}) tried to login to {current_tenant.schema_name} (ID {current_tenant.id}).")
            raise PermissionDenied("Accès refusé: Ce compte n'appartient pas à ce cabinet.")

        if current_tenant.schema_name == 'public':
            print("Warning: Login occurring on PUBLIC schema.")

        data['role'] = self.user.role
        data['clinic_id'] = self.user.clinic_id
        data['username'] = self.user.username
        return data