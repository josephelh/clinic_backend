from django.urls import path
from .views import (
    patient_list, 
    patient_detail,
    appointment_list, 
    appointment_detail,
    tooth_finding_list, 
    tooth_finding_detail,
    treatment_step_list, 
    treatment_step_detail,
    prescription_list, 
    prescription_detail
)

urlpatterns = [
    # Patients
    path('patients/', patient_list, name='patient-list'),
    path('patients/<int:pk>/', patient_detail, name='patient-detail'),

    # Appointments
    path('appointments/', appointment_list, name='appointment-list'),
    path('appointments/<int:pk>/', appointment_detail, name='appointment-detail'),

    # Tooth Findings
    path('findings/', tooth_finding_list, name='toothfinding-list'),
    path('findings/<int:pk>/', tooth_finding_detail, name='toothfinding-detail'),

    # Treatment Steps
    path('treatments/', treatment_step_list, name='treatmentstep-list'),
    path('treatments/<int:pk>/', treatment_step_detail, name='treatmentstep-detail'),

    # Prescriptions
    path('prescriptions/', prescription_list, name='prescription-list'),
    path('prescriptions/<int:pk>/', prescription_detail, name='prescription-detail'),
]
