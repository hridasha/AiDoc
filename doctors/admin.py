from django.contrib import admin
from .models import Doctor, Appointment, Prescription
# Register your models here.
admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Prescription)