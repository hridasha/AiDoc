from django.db import models
from authentication.models import CustomUser
from django.core.validators import MinValueValidator

class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient')
    full_name = models.CharField(max_length=100)
    dob = models.DateField()
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=6,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        default='other'
    )
    
    # Contact information
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Address
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    
    # Medical information
    blood_group = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-')
        ],
        null=True, blank=True, default='N/A'
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=20, null=True, blank=True)
    
    # Medical history
    medical_history = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text='Store medical conditions, surgeries, and medications in JSON format'
    )
    
    # Allergies
    allergies = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text='Store food, medication, and environmental allergies in JSON format'
    )
    
    # Profile completion status
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def save(self, *args, **kwargs):
        # Update profile completion status based on required fields
        required_fields = [
            'full_name', 'dob', 'gender', 'contact_number',
            'email', 'blood_group'
        ]
        self.is_profile_complete = all(bool(getattr(self, field)) for field in required_fields)
        super().save(*args, **kwargs)
