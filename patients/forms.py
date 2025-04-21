from django import forms
import datetime
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'dob','email','address','city','state','pincode','contact_number','emergency_contact_name','emergency_contact_relation','emergency_contact_number','weight','height']
        widgets = { 
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),  
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'})
        }
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.fields['blood_group'].choices = Patient.BLOOD_GROUP_CHOICES
            self.fields['gender'].choices = Patient.GENDER_CHOICES
            
        def clean(self):
            cleaned_data = super().clean()
            dob = cleaned_data.get('dob')
            if dob:
                age = (datetime.date.today() - dob).days // 365
                cleaned_data['age'] = age
            return cleaned_data
                