from django.urls import path, include
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('chat/', views.chat_home, name='chat'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('predict/', views.predict_disease, name='predict'),
    path('doctor/', include('doctors.urls', namespace='doctors')),
]