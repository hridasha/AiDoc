from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .forms import DoctorProfileForm
from .models import Doctor, Specialization, Appointment
from datetime import datetime, timedelta

@login_required
def doctor_profile_setup(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
        form = DoctorProfileForm(instance=doctor)
    except Doctor.DoesNotExist:
        form = DoctorProfileForm()

    if request.method == 'POST':
        if hasattr(request.user, 'doctor'):
            form = DoctorProfileForm(request.POST, instance=request.user.doctor)
        else:
            form = DoctorProfileForm(request.POST)
        
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.user = request.user
            doctor.save()
            
            # Ensure profile completion status is updated
            if doctor.is_profile_complete:
                messages.success(request, 'Profile updated successfully!')
                return redirect('doctors:doctor_dashboard')
            else:
                messages.warning(request, 'Please fill in all required fields to complete your profile.')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    return render(request, 'doctors/profile_setup.html', {
        'form': form,
        'required_fields': [
            'full_name', 'specialization', 'qualification', 'experience',
            'fee', 'working_days', 'contact_number', 'email',
            'medical_license_number', 'registration_date'
        ]
    })

@login_required
@csrf_exempt
def get_available_time_slots(request):
    try:
        doctor_id = request.GET.get('doctor_id')
        date = request.GET.get('date')
        
        if not doctor_id or not date:
            return JsonResponse({
                'error': 'Doctor ID and date are required',
                'success': False
            }, status=400)
            
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Convert date string to datetime
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Get the doctor's working hours
            if not doctor.start_time or not doctor.end_time:
                return JsonResponse({
                    'error': 'Doctor has not set working hours',
                    'success': False
                }, status=400)
                
            start_time = datetime.strptime(doctor.start_time.strftime('%H:%M'), '%H:%M').time()
            end_time = datetime.strptime(doctor.end_time.strftime('%H:%M'), '%H:%M').time()
            
            # Generate time slots (every 30 minutes)
            time_slots = []
            current_time = datetime.combine(selected_date, start_time)
            end_datetime = datetime.combine(selected_date, end_time)
            
            while current_time < end_datetime:
                # Check if this time slot is already booked
                is_booked = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=selected_date,
                    appointment_time=current_time.time()
                ).exists()
                
                time_slots.append({
                    'time': current_time.strftime('%H:%M'),
                    'is_booked': is_booked
                })
                
                current_time += timedelta(minutes=30)
            
            return JsonResponse({
                'success': True,
                'time_slots': time_slots
            })
            
        except Doctor.DoesNotExist:
            return JsonResponse({
                'error': 'Doctor not found',
                'success': False
            }, status=404)
            
    except Exception as e:
        print(f"Error getting time slots: {e}")
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

@login_required
@csrf_exempt
def book_appointment(request):
    if request.method == 'POST':
        try:
            doctor_id = request.POST.get('doctor_id')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            symptoms = request.POST.get('symptoms')
            message = request.POST.get('message', '')

            if not all([doctor_id, appointment_date, appointment_time, symptoms]):
                return JsonResponse({
                    'error': 'All fields are required',
                    'success': False
                }, status=400)

            try:
                doctor = Doctor.objects.get(id=doctor_id)
            except Doctor.DoesNotExist:
                return JsonResponse({
                    'error': 'Doctor not found',
                    'success': False
                }, status=404)

            # Check if doctor is available
            if not doctor.is_available:
                return JsonResponse({
                    'error': 'Doctor is currently not available for appointments',
                    'success': False
                }, status=400)

            # Check if the time slot is available
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).exists():
                return JsonResponse({
                    'error': 'This time slot is already booked',
                    'success': False
                }, status=400)

            # Create the appointment
            appointment = Appointment.objects.create(
                patient=request.user.patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                symptoms=symptoms,
                message=message,
                status='pending'
            )

            return JsonResponse({
                'success': True,
                'message': 'Appointment request sent successfully. Please wait for the doctor to confirm.',
                'appointment_id': appointment.id
            })

        except Exception as e:
            print(f"Error booking appointment: {e}")
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)

    return JsonResponse({
        'error': 'Only POST requests are allowed',
        'success': False
    }, status=405)

@login_required
def edit_profile(request):
    doctor = Doctor.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('doctors:doctor_dashboard')
    else:
        form = DoctorProfileForm(instance=doctor)
    
    return render(request, 'doctors/edit_profile.html', {
        'form': form
    })

@login_required
def profile_setup(request):
    if hasattr(request.user, 'doctor'):
        return redirect('doctors:doctor_dashboard')

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.user = request.user
            doctor.save()
            messages.success(request, 'Your profile has been set up successfully.')
            return redirect('doctors:doctor_dashboard')
    else:
        form = DoctorProfileForm()
    
    return render(request, 'doctors/profile_setup.html', {
        'form': form
    })

def doctor_list(request):
    try:
        specialist = request.GET.get('specialist', '').strip()
        if not specialist:
            return JsonResponse({'error': 'Specialist parameter is required'}, status=400)

        # Get the specialization object
        specialization = Specialization.objects.filter(name__iexact=specialist).first()
        if not specialization:
            return JsonResponse([], safe=False)

        # Get doctors for this specialization who are available
        doctors = Doctor.objects.filter(
            specialization=specialization,
            is_available=True
        ).values(
            'id',
            'full_name',
            'experience',
            'total_reviews'
        )

        if not doctors.exists():
            return JsonResponse([], safe=False)

        doctor_list = [
            {
                'id': doc['id'],
                'name': doc['full_name'],
                'specialist': specialist,
                'experience': doc['experience'] if doc['experience'] else 0,
                'rating': round((doc['total_reviews'] / 5) if doc['total_reviews'] > 0 else 0, 1)
            }
            for doc in doctors
        ]
        
        return JsonResponse(doctor_list, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def doctor_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.profile_completed:
        return redirect("profile_setup")
    return render(request, "doctors/dashboard.html")
