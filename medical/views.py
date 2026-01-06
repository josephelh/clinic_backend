from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Patient, Appointment
from .serializers import PatientSerializer, AppointmentSerializer


# Patient views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_list(request):
    patients = Patient.objects.prefetch_related('toothfinding_set').all()
    serializer = PatientSerializer(patients, many=True, context={'request': request})
    return Response(serializer.data)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def patient_create(request):
    serializer = PatientSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def patient_detail(request, pk):
    patient = get_object_or_404(Patient.objects.prefetch_related('toothfinding_set'), pk=pk)
    
    if request.method == 'GET':
        serializer = PatientSerializer(patient, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = PatientSerializer(patient, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Appointment views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointment_list_create(request):
    if request.method == 'GET':
        user = request.user
        
        # 1. Admin and Assistants see every appointment in the current schema
        if user.role in ['ADMIN', 'ASSISTANT']:
            appointments = Appointment.objects.select_related('patient', 'doctor').all()
        else:
            # 2. Doctors only see appointments assigned to them
            appointments = Appointment.objects.select_related('patient', 'doctor').filter(doctor=user)
        
        serializer = AppointmentSerializer(appointments, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def appointment_detail(request, pk):
    user = request.user
    
    # Get appointment with role-based filtering
    if user.role in ['ADMIN', 'ASSISTANT']:
        appointment = get_object_or_404(
            Appointment.objects.select_related('patient', 'doctor'), 
            pk=pk
        )
    else:
        appointment = get_object_or_404(
            Appointment.objects.select_related('patient', 'doctor'), 
            pk=pk, 
            doctor=user
        )
    
    if request.method == 'GET':
        serializer = AppointmentSerializer(appointment, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = AppointmentSerializer(appointment, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        appointment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

