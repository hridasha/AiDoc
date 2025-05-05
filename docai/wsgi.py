"""
WSGI config for docai project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


# Check if the model is installed
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')  # Replace with your model
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docai.settings')

application = get_wsgi_application()

