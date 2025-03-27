from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('profile_setup/', views.doctor_profile_setup, name='profile_setup'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('list/', views.doctor_list, name='doctor_list'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('get_time_slots/', views.get_available_time_slots, name='get_available_time_slots'),
    path('manage_appointments/', views.manage_appointments, name='manage_appointments'),
]