from django.urls import path
from django.contrib.auth import views 
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='dashboard'),
    path('profile_setup/', views.patient_profile_setup, name='patient_profile_setup'),
    path('profile/', views.patient_profile, name='patient_profile'),
    path('appointment/<int:doctor_id>/', views.appointment_booking, name='appointment_booking'),
    path('view_appointments/', views.view_appointments, name='view_appointments'),
    path('prescription/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
    path('view_prescription/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
    path('profile-update/', views.patient_profile_update, name='patient_profile_update'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
]
