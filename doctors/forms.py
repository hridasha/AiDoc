from django import forms
from .models import Doctor, Specialization

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = [
            'user', 'total_reviews', 'is_available',
            'is_profile_complete', 'is_verified', 'created_at', 'updated_at'
        ]
        fields = [
            'full_name', 'specialization', 'qualification', 'experience', 
            'fee', 'working_days', 'contact_number', 'email', 
            'city', 'state', 'pincode', 
            'medical_license_number', 'registration_date',
            'start_time', 'end_time', 'availability_notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'working_days': forms.Select(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'availability_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialization'].queryset = Specialization.objects.filter(is_active=True)
        self.fields['working_days'].choices = Doctor.WORKING_DAYS_CHOICES

    def clean(self):
        cleaned_data = super().clean()
        specialization = cleaned_data.get('specialization')
        if not specialization:
            raise forms.ValidationError('Specialization is required')
        return cleaned_data