from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('profile/', views.doctor_dashboard, name='doctor_dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('list/', views.doctor_list, name='doctor_list'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
]
