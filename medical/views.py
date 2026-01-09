from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from .models import Patient, Appointment, ToothFinding, TreatmentStep, Prescription
from .serializers import (
    PatientDetailSerializer, 
    AppointmentSerializer, 
    ToothFindingSerializer, 
    TreatmentStepSerializer, 
    PrescriptionSerializer,
    PatientListSerializer
)

# --------------------------
# Patient Views
# --------------------------

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20 # Only 20 patients per "page" for tablet performance
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def patient_list(request):
    if request.method == 'GET':
        # 1. STOP prefetching findings. It's not needed for the list.
        # 2. Add select_related or only() to optimize DB query
        patients = Patient.objects.all().order_by('-id')
        
        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            patients = patients.filter(
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(cin__icontains=search_query)
            )

        # 3. Use Pagination
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(patients, request)
        
        # 4. Use the LIGHTWEIGHT Serializer
        serializer = PatientListSerializer(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        # Create still uses the full serializer or a specific creation one
        serializer = PatientDetailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def patient_detail(request, pk):
    """
    Retrieve, update or delete a patient instance.
    """
    patient = get_object_or_404(Patient.objects.prefetch_related('findings'), pk=pk)
    
    if request.method == 'GET':
        serializer = PatientDetailSerializer(patient, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = PatientDetailSerializer(patient, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        patient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------
# Appointment Views
# --------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointment_list(request):
    """
    List appointments (with RBAC) or create a new appointment.
    """
    user = request.user
    
    # Base QuerySet with optimizations
    qs = Appointment.objects.select_related('patient', 'doctor').prefetch_related('treatment_steps')
    
    if request.method == 'GET':
        # RBAC Logic
        if user.role in ['ADMIN', 'ASSISTANT']:
            appointments = qs.all()
        else:
            # Doctor sees only their own appointments
            appointments = qs.filter(doctor=user)
            
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
    """
    Retrieve, update or delete an appointment instance (with RBAC).
    """
    user = request.user
    qs = Appointment.objects.select_related('patient', 'doctor').prefetch_related('treatment_steps')

    # RBAC Logic for retrieval
    if user.role in ['ADMIN', 'ASSISTANT']:
        appointment = get_object_or_404(qs, pk=pk)
    else:
        # Doctor sees only their own appointments
        appointment = get_object_or_404(qs, pk=pk, doctor=user)
    
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


# --------------------------
# Tooth Finding Views
# --------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tooth_finding_list(request):
    """
    List FDI tooth findings or create a new one.
    """
    if request.method == 'GET':
        findings = ToothFinding.objects.all()
        serializer = ToothFindingSerializer(findings, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ToothFindingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tooth_finding_detail(request, pk):
    """
    Retrieve, update or delete a tooth finding.
    """
    finding = get_object_or_404(ToothFinding, pk=pk)
    
    if request.method == 'GET':
        serializer = ToothFindingSerializer(finding, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ToothFindingSerializer(finding, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        finding.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------
# Treatment Step Views
# --------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def treatment_step_list(request):
    """
    List treatment steps (optionally filtered by patient) or create a new one.
    Query Param: ?patient=<id>
    """
    if request.method == 'GET':
        queryset = TreatmentStep.objects.select_related('appointment', 'appointment__patient').all()
        
        # Filter by patient if provided
        patient_id = request.query_params.get('patient')
        if patient_id:
            queryset = queryset.filter(appointment__patient_id=patient_id)
            
        serializer = TreatmentStepSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = TreatmentStepSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def treatment_step_detail(request, pk):
    """
    Retrieve, update or delete a treatment step.
    """
    step = get_object_or_404(TreatmentStep, pk=pk)
    
    if request.method == 'GET':
        serializer = TreatmentStepSerializer(step, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = TreatmentStepSerializer(step, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        step.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --------------------------
# Prescription Views
# --------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def prescription_list(request):
    """
    List prescriptions or create a new one.
    """
    if request.method == 'GET':
        prescriptions = Prescription.objects.all()
        serializer = PrescriptionSerializer(prescriptions, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = PrescriptionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def prescription_detail(request, pk):
    """
    Retrieve, update or delete a prescription.
    """
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if request.method == 'GET':
        serializer = PrescriptionSerializer(prescription, context={'request': request})
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = PrescriptionSerializer(prescription, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        prescription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
