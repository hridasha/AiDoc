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
    path('create_prescription/<int:appointment_id>/', views.create_prescription, name='create_prescription'),
    path('view_prescription/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
    path('edit_prescription/<int:prescription_id>/', views.edit_prescription, name='edit_prescription'),
    path('book_appointments_by_search/', views.book_appointments_by_search, name='book_appointments_by_search'),
    # path('video_consultation/<int:appointment_id>/', views.video_consultation, name='video_consultation'),
]