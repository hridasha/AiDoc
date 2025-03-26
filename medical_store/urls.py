from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("dashboard/", views.medical_store_dashboard, name="medical_store_dashboard"),
    path("profile_setup/", views.medical_store_profile_setup, name="medical_store_profile_setup"),
]
