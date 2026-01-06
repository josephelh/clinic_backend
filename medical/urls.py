from django.urls import path
from .views import (
    patient_list,
    patient_create,
    patient_detail,
    appointment_list_create,
    appointment_detail
)

urlpatterns = [
    path('patients/', patient_list, name='patient-list'),
    path('patients/create/', patient_create, name='patient-create'),

    path('patients/<int:pk>/', patient_detail, name='patient-detail'),
    path('appointments/', appointment_list_create, name='appointment-list'),
    path('appointments/<int:pk>/', appointment_detail, name='appointment-detail'),
    
]