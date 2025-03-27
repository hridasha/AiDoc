from django.urls import path
from django.contrib.auth import views 
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("", views.user_login, name="user_login"),
    path("logout/", views.user_logout, name="logout"),
    path("profile_setup/", views.profile_setup, name="profile_setup"),
]
