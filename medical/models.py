from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64

# Simple helper for encryption/decryption
# In a real production app, you would put the KEY in your .env file
SECRET_KEY_FOR_ENCRYPTION = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32))
cipher_suite = Fernet(SECRET_KEY_FOR_ENCRYPTION)

class EncryptedCharField(models.CharField):
    """Custom field that encrypts data before saving to DB"""
    def get_prep_value(self, value):
        if value:
            return cipher_suite.encrypt(value.encode()).decode()
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            try:
                return cipher_suite.decrypt(value.encode()).decode()
            except:
                return value # Return as is if decryption fails
        return value

class Patient(models.Model):
    INSURANCE_CHOICES = (
        ('AMO', 'AMO (CNSS/CNOPS)'),
        ('MUTUELLE', 'Mutuelle Privée'),
        ('MUTUELLE_FAR', 'Mutuelle Far'),
        ('NONE', 'Sans Assurance'),
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    def __str__(self):
        return self.full_name
    # We use our custom EncryptedCharField here
    cin = EncryptedCharField(max_length=255, null=True, blank=True)
    
    phone = models.CharField(max_length=20)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_CHOICES, default='NONE')
    insurance_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    Subject = models.CharField(max_length=200)
    StartTime = models.DateTimeField()
    EndTime = models.DateTimeField()
    Description = models.TextField(blank=True)
    Status = models.CharField(max_length=50, default='Scheduled')
    CategoryColor = models.CharField(max_length=7, default='#0077BE')
    tooth_number = models.IntegerField(null=True, blank=True)

class ToothFinding(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    tooth_number = models.IntegerField() 
    condition = models.CharField(max_length=50)
    surface = models.CharField(max_length=10, blank=True) 
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TreatmentStep(models.Model):
    """Track sequential treatment actions on a specific tooth per appointment"""
    STEP_CHOICES = [
        ('diagnosis', 'Diagnosis'),
        ('cleaning', 'Cleaning'),
        ('filling', 'Filling'),
        ('root_canal', 'Root Canal'),
        ('extraction', 'Extraction'),
        ('crown', 'Crown/Cap'),
        ('followup', 'Follow-up'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='treatment_steps')
    tooth_number = models.CharField(max_length=2)  # FDI notation
    step_type = models.CharField(max_length=20, choices=STEP_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment__StartTime', 'created_at']
    
    def __str__(self):
        return f"Tooth {self.tooth_number} - {self.step_type} on {self.appointment.StartTime.date()}"