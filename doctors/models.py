from django.db import models
from authentication.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta

class Specialization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    # Working days choices
    WORKING_DAYS_CHOICES = [
        ('custom', 'Custom Days'),
        ('mon-fri', 'Monday to Friday'),
        ('mon-sat', 'Monday to Saturday'),
        ('tue-sun', 'Tuesday to Sunday'),
        ('mon-sun', 'Monday to Sunday'),
        ('alternate', 'Alternate Days'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor')
    full_name = models.CharField(max_length=100)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, related_name='doctors')
    qualification = models.CharField(max_length=200, null=True, blank=True)
    experience = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    total_reviews = models.IntegerField(default=0)
    address = models.TextField(null=True, blank=True)
    start_time = models.TimeField(default='10:00')
    end_time = models.TimeField(default='18:00')
    working_days = models.CharField(
        max_length=20,
        choices=WORKING_DAYS_CHOICES,
        default='mon-fri'
    )
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    availability_notes = models.TextField(blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    medical_license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    is_profile_complete = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.full_name}"

    def get_available_time_slots(self, date):
        """
        Get available time slots for a specific date
        """
        # Get all appointments for this doctor on the given date
        booked_slots = Appointment.objects.filter(
            doctor=self,
            appointment_date=date
        ).values_list('appointment_time', flat=True)

        # Generate time slots from start_time to end_time
        current_time = self.start_time
        time_slots = []
        
        while current_time < self.end_time:
            # Format time as HH:MM
            time_slot = current_time.strftime('%H:%M')
            
            # Check if this time slot is already booked
            if time_slot not in [t.strftime('%H:%M') for t in booked_slots]:
                time_slots.append(time_slot)
            
            # Move to next 30-minute slot
            current_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=30)).time()
        
        return time_slots

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'

    def save(self, *args, **kwargs):
        required_fields = [
            'full_name', 'specialization', 'qualification', 'experience',
            'fee', 'working_days', 'contact_number', 'email',
            'medical_license_number', 'registration_date'
        ]
        self.is_profile_complete = all(bool(getattr(self, field)) for field in required_fields)
        
        super().save(*args, **kwargs)

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Request'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ]

    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reason_for_rejection = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.full_name} on {self.appointment_date} ({self.get_status_display()})"

@receiver(post_save, sender=CustomUser)
def create_doctor(sender, instance, created, **kwargs):
    if created and instance.role == 'doctor':
        Doctor.objects.create(
            user=instance,
            full_name=instance.username,
            email=instance.email,
            contact_number='', 
            city='',
            state='',
            pincode='',
            medical_license_number='', 
            registration_date=instance.date_joined.date()
        )

@receiver(post_save, sender=Doctor)
def update_user_profile_status(sender, instance, **kwargs):
    """Update the user's profile completion status when doctor profile is saved"""
    if instance.user and instance.is_profile_complete != instance.user.profile_completed:
        instance.user.profile_completed = instance.is_profile_complete
        instance.user.save()
