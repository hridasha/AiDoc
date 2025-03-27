"""
URL configuration for docai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),  # Redirect root to login
    path('', include('authentication.urls')),  # User registration & login
    path('patient/', include('patients.urls')),  # Patient dashboard & profile setup
    path('doctor/', include('doctors.urls')),  # Doctor dashboard & profile setup
    path('medical_store/', include('medical_store.urls')),  # Medical store dashboard & profile setup
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),  # Chatbot
]
