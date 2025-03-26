from django.urls import path
from django.contrib.auth import views 
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='dashboard'),
    path('profile_setup/', views.patient_profile_setup, name='patient_profile_setup'),
    path('profile/', views.patient_profile, name='patient_profile'),
]
