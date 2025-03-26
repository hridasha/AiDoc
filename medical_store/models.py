from django.db import models
from authentication.models import CustomUser
from django.core.validators import MinValueValidator

class MedicalStore(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='medical_store')
    store_name = models.CharField(max_length=100)
    store_type = models.CharField(
        max_length=20,
        choices=[
            ('retail', 'Retail'),
            ('wholesale', 'Wholesale'),
            ('both', 'Both')
        ],
        default='retail'
    )
    
    # Registration details
    license_number = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    registration_date = models.DateField()
    
    # Contact information
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Operating hours
    operating_days = models.CharField(
        max_length=100,
        choices=[
            ('mon-fri', 'Monday to Friday'),
            ('mon-sat', 'Monday to Saturday'),
            ('all', 'All Days'),
            ('custom', 'Custom Days')
        ],
        default='mon-sat'
    )
    opening_time = models.TimeField(default='09:00')
    closing_time = models.TimeField(default='21:00')
    
    # Store details
    number_of_employees = models.IntegerField(default=1)
    store_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    
    # Special features
    has_home_delivery = models.BooleanField(default=False)
    has_online_ordering = models.BooleanField(default=False)
    accepts_insurance = models.BooleanField(default=False)
    
    # Inventory management
    inventory_management_system = models.BooleanField(default=False)
    has_pharmacist = models.BooleanField(default=False)
    
    # Profile completion status
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Store'
        verbose_name_plural = 'Medical Stores'

    def save(self, *args, **kwargs):
        # Update profile completion status based on required fields
        required_fields = [
            'store_name', 'store_type', 'license_number',
            'registration_number', 'registration_date',
            'contact_number', 'email', 'address',
            'city', 'state', 'pincode'
        ]
        self.is_profile_complete = all(bool(getattr(self, field)) for field in required_fields)
        super().save(*args, **kwargs)
