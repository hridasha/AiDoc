from django.shortcuts import render, redirect
from doctors.models import Prescription
from doctors.views import get_available_time_slots
from .models import Patient
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.decorators import login_required
from functools import wraps
from doctors.models import Doctor, Appointment
from doctors.views import get_available_time_slots

def profile_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('user_login')
        if not hasattr(request.user, 'profile_completed') or not request.user.profile_completed:
            return redirect('profile_setup')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def patient_profile_setup(request):
    if request.method == "POST":
        try:
            # Check if patient profile already exists
            if hasattr(request.user, 'patient'):
                messages.error(request, "You already have a patient profile. Please update your existing profile instead.")
                return redirect("patients:dashboard")

            full_name = request.POST['full_name']
            dob = request.POST['dob']
            gender = request.POST['gender']
            contact_number = request.POST['contact_number']
            email = request.POST['email']
            
            # Convert DOB string to date object
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            
            # Calculate age from DOB
            today = datetime.now().date()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            if age < 0 or age > 150:
                messages.error(request, "Please enter a valid date of birth")
                return render(request, "patients/profile_setup.html")
            
            patient = Patient(
                user=request.user,
                full_name=full_name,
                dob=dob_date,
                gender=gender,
                contact_number=contact_number,
                email=email,
                age=age
            )
            patient.save()

            request.user.profile_completed = True
            request.user.save()
            
            return redirect("patients:dashboard")
            
        except KeyError as e:
            messages.error(request, f"Missing required field: {str(e)}")
            return render(request, "patients/profile_setup.html")
        except ValueError:
            messages.error(request, "Please enter a valid date format (YYYY-MM-DD)")
            return render(request, "patients/profile_setup.html")
            
    return render(request, "patients/profile_setup.html")


def patient_profile_update(request):
    return render(request, "patients/profile.html")

@login_required
@profile_required
def patient_dashboard(request):
    return render(request, "patients/dashboard.html")

@profile_required
def patient_profile(request):
    patient = request.user.patient
    context ={
        'patient': patient,
    }
    return render(request, "patients/profile.html")

@login_required
def appointment_booking(request, doctor_id):
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        if request.method == 'POST':
            appointment_date = request.POST.get('appointment_date')
            time_slot = request.POST.get('time_slot')
            symptoms = request.POST.get('symptoms')
            message = request.POST.get('message', '')
            
            if not appointment_date or not time_slot or not symptoms:
                messages.error(request, 'Please fill in all required fields')
                return redirect('patients:appointment_booking', doctor_id=doctor_id)
            
            # Check if the time slot is already requested
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time__hour=int(time_slot.split(':')[0]),
                appointment_time__minute=int(time_slot.split(':')[1]),
                status__in=['pending', 'approved']
            ).exists():
                messages.error(request, 'This time slot already has a pending request')
                return redirect('patients:appointment_booking', doctor_id=doctor_id)
            
            # Create the appointment request
            appointment = Appointment(
                patient=request.user.patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=datetime.strptime(time_slot, '%H:%M').time(),
                symptoms=symptoms,
                message=message,
                status='pending'
            )
            appointment.save()
            
            messages.success(request, 'Appointment request submitted successfully! The doctor will review your request.')
            return redirect('patients:dashboard')
            
        # Get the selected date from GET parameters or use today's date
        selected_date = request.GET.get('date')
        if not selected_date:
            selected_date = datetime.now().date()
        else:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        
        # Get available time slots for the selected date
        available_slots = doctor.get_available_time_slots(selected_date)
        
        return render(request, 'patients/appointment_booking.html', {
            'doctor': doctor,
            'available_slots': available_slots,
            'selected_date': selected_date
        })
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor not found')
        return redirect('patients:doctor_list')

@login_required
def view_appointments(request):
    try:
        patient = request.user.patient
        
        # Get all appointments for this patient
        appointments = Appointment.objects.filter(
            patient=patient
        ).order_by('-appointment_date', '-appointment_time')
        
        return render(request, 'patients/view_appointments.html', {
            'appointments': appointments
        })
    except Patient.DoesNotExist:
        messages.error(request, 'Patient profile not found')
        return redirect('patients:patient_profile_setup')
    
@login_required
def view_prescription(request, prescription_id):
    try:
        prescription = Prescription.objects.get(
            id=prescription_id,
            appointment__patient=request.user.patient
        )
        prescribed_medicines = prescription.prescribedmedicine_set.all()
        
        return render(request, 'patients/view_prescription.html', {
            'prescription': prescription,
            'prescribed_medicines': prescribed_medicines
        })
        
    except Prescription.DoesNotExist:
        messages.error(request, 'Prescription not found')
        return redirect('patients:view_appointments')