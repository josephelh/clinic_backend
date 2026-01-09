from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import datetime
import hashlib

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
        ('AMO', 'AMO'),
        ('MUTUELLE', 'Mutuelle Privée'),
        ('MUTUELLE_FAR', 'Mutuelle FAR'),
        ('NONE', 'Sans'),
    )

    GENDER_CHOICES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Medical Safety Hub
    medical_alerts = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    is_high_risk = models.BooleanField(default=False)

    # Privacy Fields
    cin = EncryptedCharField(max_length=255, null=True, blank=True)
    cin_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    
    phone = EncryptedCharField(max_length=255)
    phone_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    insurance_type = models.CharField(max_length=20, choices=INSURANCE_CHOICES, default='NONE')
    insurance_id = EncryptedCharField(max_length=255, null=True, blank=True)
    insurance_id_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.cin:
            self.cin_hash = hashlib.sha256(self.cin.strip().encode()).hexdigest()
        else:
            self.cin_hash = None
            
        if self.phone:
            self.phone_hash = hashlib.sha256(self.phone.strip().encode()).hexdigest()
        else:
            self.phone_hash = None

        if self.insurance_id:
            self.insurance_id_hash = hashlib.sha256(self.insurance_id.strip().encode()).hexdigest()
        else:
            self.insurance_id_hash = None
            
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
        
    def __str__(self):
        return self.full_name

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    Subject = models.CharField(max_length=200)
    StartTime = models.DateTimeField()
    EndTime = models.DateTimeField()
    Description = models.TextField(blank=True)
    Status = models.CharField(max_length=50, default='Scheduled')
    CategoryColor = models.CharField(max_length=7, default='#0077BE')

    def __str__(self):
        return f"{self.Subject} ({self.StartTime})"

class ToothFinding(models.Model):
    CONDITION_CHOICES = [
        ('CARIES', 'Carie'),
        ('MISSING', 'Absente'),
        ('FILLING', 'Obturation'),
        ('CROWN', 'Couronne'),
        ('IMPLANT', 'Implant'),
        ('ROOT_CANAL', 'Dévitalisée'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='findings')
    tooth_number = models.IntegerField() # FDI 11-48
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    surface = models.CharField(max_length=10, blank=True) 
    notes = models.TextField(blank=True)
    found_in = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='discovered_findings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tooth {self.tooth_number}: {self.condition} ({self.patient})"


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
    tooth_number = models.IntegerField()
    step_type = models.CharField(max_length=20, choices=STEP_CHOICES)
    description = models.TextField(blank=True)
    
    # Cost tracking
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment__StartTime', 'created_at']
    
    def __str__(self):
        return f"Tooth {self.tooth_number} - {self.step_type} on {self.appointment.StartTime.date()}"

class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    medications = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.patient.full_name} on {self.created_at.date()}"
