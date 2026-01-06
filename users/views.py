from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.db import connection
from .models import User
from .serializers import CustomTokenObtainPairSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    # Filter users by the current tenant's clinic ID
    current_tenant = connection.tenant
    
    # If we are in a tenant schema, only show users belonging to this clinic
    if current_tenant.schema_name != 'public':
        queryset = User.objects.filter(clinic_id=current_tenant.id)
    else:
        # In public schema, maybe show all or filter differently
        queryset = User.objects.all()
    
    role = request.query_params.get('role')
    if role:
        queryset = queryset.filter(role=role)
    
    serializer = UserSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    # Filter users by the current tenant's clinic ID
    current_tenant = connection.tenant
    
    # If we are in a tenant schema, only show users belonging to this clinic
    if current_tenant.schema_name != 'public':
        user = get_object_or_404(User, pk=pk, clinic_id=current_tenant.id)
    else:
        user = get_object_or_404(User, pk=pk)
    
    serializer = UserSerializer(user)
    return Response(serializer.data)