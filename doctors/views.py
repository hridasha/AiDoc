from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .forms import DoctorProfileForm
from .models import Doctor, Specialization

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
def book_appointment(request):
    if request.method == 'POST':
        try:
            doctor_id = request.POST.get('doctor_id')
            if not doctor_id:
                return JsonResponse({'error': 'Doctor ID is required'}, status=400)

            doctor = Doctor.objects.get(id=doctor_id)
            return JsonResponse({
                'message': f'Appointment booked successfully with Dr. {doctor.full_name}'
            })
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctor not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

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

def doctor_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.profile_completed:
        return redirect("profile_setup")
    return render(request, "doctors/dashboard.html")
