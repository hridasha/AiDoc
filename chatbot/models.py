from django.db import models
from patients.models import Patient

# Create your models here.

class ChatbotQuery(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    disease_predicted = models.CharField(max_length=100, null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    specialist_suggested = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.patient.user.username} - {self.created_at}"
