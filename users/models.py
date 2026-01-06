from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('DOCTOR', 'Doctor'),
        ('ASSISTANT', 'Assistant'),
        ('ADMIN', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='ASSISTANT')
    # Link to clinic for easier reference in single-domain views
    clinic_id = models.IntegerField(null=True, blank=True)