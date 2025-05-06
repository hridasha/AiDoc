from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .forms import DoctorProfileForm
from .models import Doctor, Specialization, Appointment, Prescription, PrescribedMedicine
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
def get_available_time_slots(request):
    try:
        print(f"Request received: {request.method} {request.path}")
        print(f"Request data: {dict(request.GET)}")
        
        doctor_id = request.GET.get('doctor_id')
        date = request.GET.get('date')
        
        if not doctor_id or not date:
            print("Error: Missing doctor_id or date")
            return JsonResponse({
                'error': 'Doctor ID and date are required',
                'success': False
            }, status=400)
            
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            print(f"Found doctor: {doctor.full_name}")
            
            # Convert date string to datetime
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            print(f"Selected date: {selected_date}")
            
            # Get the doctor's working hours
            if not doctor.start_time or not doctor.end_time:
                print("Error: Doctor has no working hours set")
                return JsonResponse({
                    'error': 'Doctor has not set working hours',
                    'success': False
                }, status=400)
            
            print(f"Doctor working hours: {doctor.start_time} to {doctor.end_time}")
            
            start_time = datetime.strptime(doctor.start_time.strftime('%H:%M'), '%H:%M').time()
            end_time = datetime.strptime(doctor.end_time.strftime('%H:%M'), '%H:%M').time()
            
            # Generate time slots (every 30 minutes)
            time_slots = []
            current_time = datetime.combine(selected_date, start_time)
            end_datetime = datetime.combine(selected_date, end_time)
            
            print(f"Generating time slots from {start_time} to {end_time}")
            
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
            
            print(f"Generated {len(time_slots)} time slots")
            
            return JsonResponse({
                'success': True,
                'time_slots': time_slots
            })
            
        except Doctor.DoesNotExist:
            print(f"Error: Doctor with ID {doctor_id} not found")
            return JsonResponse({
                'error': 'Doctor not found',
                'success': False
            }, status=404)
            
    except Exception as e:
        print(f"Error getting time slots: {str(e)}")
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

            # Create the appointment request
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
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found')
        return redirect('doctors:doctor_dashboard')
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('doctors:doctor_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
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

@login_required
def manage_appointments(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
        
        if request.method == 'POST':
            appointment_id = request.POST.get('appointment_id')
            action = request.POST.get('action')
            reason = request.POST.get('reason', '')
            
            try:
                appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
                
                if action == 'approve':
                    appointment.status = 'approved'
                    appointment.save()
                    
                    # Send email notification
                    send_appointment_approval_email(appointment)
                    
                    messages.success(request, 'Appointment request approved successfully!')
                elif action == 'reject':
                    appointment.status = 'rejected'
                    appointment.reason_for_rejection = reason
                    appointment.save()
                    messages.success(request, 'Appointment request rejected successfully!')
                elif action == 'prescribe':
                    return redirect('doctors:create_prescription', appointment_id=appointment_id)
                
                return redirect('doctors:manage_appointments')
                
            except Appointment.DoesNotExist:
                messages.error(request, 'Appointment not found')
                return redirect('doctors:manage_appointments')
        
        pending_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='pending'
        ).order_by('appointment_date', 'appointment_time')
        
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='approved',
            appointment_date__gte=datetime.now().date()
        ).order_by('appointment_date', 'appointment_time')
        
        return render(request, 'doctors/manage_appointments.html', {
            'pending_appointments': pending_appointments,
            'upcoming_appointments': upcoming_appointments
        })
        
    except Doctor.DoesNotExist:
        messages.error(request, 'Access denied')
        return redirect('doctors:profile_setup')

@login_required
def create_prescription(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id, doctor=request.user.doctor)
        
        # Check if prescription already exists
        if hasattr(appointment, 'prescription'):
            messages.error(request, 'A prescription already exists for this appointment')
            return redirect('doctors:view_prescription', prescription_id=appointment.prescription.id)
        
        if request.method == 'POST':
            diagnosis = request.POST.get('diagnosis', '')
            notes = request.POST.get('notes', '')
            
            # Create prescription
            prescription = Prescription.objects.create(
                appointment=appointment,
                diagnosis=diagnosis,
                notes=notes
            )
            
            # Add prescribed medicines
            for i in range(int(request.POST.get('medicine_count', 0))):
                medicine_name = request.POST.get(f'medicine_name_{i}')
                generic_name = request.POST.get(f'generic_name_{i}', '')
                dosage_form = request.POST.get(f'dosage_form_{i}')
                strength = request.POST.get(f'strength_{i}')
                dosage = request.POST.get(f'dosage_{i}')
                frequency = request.POST.get(f'frequency_{i}')
                duration = request.POST.get(f'duration_{i}')
                instructions = request.POST.get(f'instructions_{i}', '')
                
                if medicine_name and dosage_form and strength and dosage and frequency and duration:
                    # Add to prescription
                    PrescribedMedicine.objects.create(
                        prescription=prescription,
                        medicine_name=medicine_name,
                        generic_name=generic_name,
                        dosage_form=dosage_form,
                        strength=strength,
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        instructions=instructions
                    )
            
            messages.success(request, 'Prescription created successfully!')
            return redirect('doctors:view_prescription', prescription_id=prescription.id)
            
        return render(request, 'doctors/create_prescription.html', {
            'appointment': appointment
        })
        
    except Appointment.DoesNotExist:
        messages.error(request, 'Invalid appointment')
        return redirect('doctors:manage_appointments')
    
@login_required
def view_prescription(request, prescription_id):
    try:
        # First check if the user is a doctor
        if not hasattr(request.user, 'doctor'):
            messages.error(request, 'Access denied. Only doctors can view prescriptions.')
            return redirect('doctors:manage_appointments')
        
        # Get the prescription
        prescription = Prescription.objects.get(
            id=prescription_id,
            appointment__doctor=request.user.doctor
        )
        
        # Get all prescribed medicines and filter out any that might have issues
        prescribed_medicines = []
        for medicine in prescription.prescribedmedicine_set.all():
            try:
                # Check if the medicine has all required fields
                if hasattr(medicine, 'medicine_name') and hasattr(medicine, 'strength'):
                    prescribed_medicines.append(medicine)
            except AttributeError:
                continue
        
        return render(request, 'doctors/view_prescription.html', {
            'prescription': prescription,
            'prescribed_medicines': prescribed_medicines
        })
        
    except Prescription.DoesNotExist:
        messages.error(request, 'Prescription not found')
        return redirect('doctors:manage_appointments')
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found')
        return redirect('doctors:manage_appointments')

@login_required
def edit_prescription(request, prescription_id):
    try:
        appointment = Appointment.objects.get(id=prescription_id, doctor=request.user.doctor)
        
        # Check if prescription already exists
        if not hasattr(appointment, 'prescription'):
            messages.error(request, 'No prescription exists for this appointment')
            return redirect('doctors:create_prescription', appointment_id=appointment.id)
        
        # Get the prescription
        prescription = appointment.prescription
        
        if request.method == 'POST':
            diagnosis = request.POST.get('diagnosis', '')
            notes = request.POST.get('notes', '')
            
            # Update prescription
            prescription.diagnosis = diagnosis
            prescription.notes = notes
            prescription.save()
            
            # Delete existing medicines
            prescription.prescribedmedicine_set.all().delete()
            
            # Get the total number of medicines from the form
            medicine_count = int(request.POST.get('medicine_count', 0))
            
            # Add new medicines
            for i in range(medicine_count):
                medicine_name = request.POST.get(f'medicine_name_{i}')
                generic_name = request.POST.get(f'generic_name_{i}', '')
                dosage_form = request.POST.get(f'dosage_form_{i}')
                strength = request.POST.get(f'strength_{i}')
                dosage = request.POST.get(f'dosage_{i}')
                frequency = request.POST.get(f'frequency_{i}')
                duration = request.POST.get(f'duration_{i}')
                instructions = request.POST.get(f'instructions_{i}', '')
                
                # Only create medicine if all required fields are present
                if medicine_name and dosage_form and strength and dosage and frequency and duration:
                    PrescribedMedicine.objects.create(
                        prescription=prescription,
                        medicine_name=medicine_name,
                        generic_name=generic_name,
                        dosage_form=dosage_form,
                        strength=strength,
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        instructions=instructions
                    )
            
            messages.success(request, 'Prescription updated successfully!')
            return redirect('doctors:view_prescription', prescription_id=prescription.id)
            
        # For GET request
        prescribed_medicines = prescription.prescribedmedicine_set.all()
        return render(request, 'doctors/edit_prescription.html', {
            'prescription': prescription,
            'prescribed_medicines': prescribed_medicines
        })
        
    except Appointment.DoesNotExist:
        messages.error(request, 'Invalid appointment')
        return redirect('doctors:manage_appointments')
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found')
        return redirect('doctors:manage_appointments')

@login_required
def book_appointments_by_search(request):
    if request.method == 'GET':
        search_query = request.GET.get('query', '')
        doctors = Doctor.objects.filter(
            Q(full_name__icontains=search_query) | 
            Q(specialization__name__icontains=search_query)
        ).filter(is_available=True, is_profile_complete=True)
        
        # Get today's date for time slots
        today = datetime.now().date()
        
        # Prepare time slots for each doctor
        doctors_with_slots = []
        for doctor in doctors:
            time_slots = []
            if doctor.start_time and doctor.end_time:
                current_time = datetime.combine(today, doctor.start_time)
                end_time = datetime.combine(today, doctor.end_time)
                
                while current_time < end_time:
                    # Check if this time slot is already booked
                    is_booked = Appointment.objects.filter(
                        doctor=doctor,
                        appointment_date=today,
                        appointment_time=current_time.time()
                    ).exists()
                    
                    time_slots.append({
                        'time': current_time.strftime('%H:%M'),
                        'is_booked': is_booked
                    })
                    
                    current_time += timedelta(minutes=30)
            
            doctors_with_slots.append({
                'doctor': doctor,
                'time_slots': time_slots
            })
            
        if not doctors.exists() and search_query:
            messages.warning(request, 'No doctors found matching your search criteria.')
            
        return render(
            request, 'doctors/book_appointment_by_search.html', {
                'doctors': doctors_with_slots,
                'search_query': search_query,
                'today': today
            }
        )
    
    elif request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        if not doctor_id:
            messages.error(request, 'Please select a doctor first')
            return redirect('doctors:book_appointments_by_search')
            
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            appointment_date = request.POST.get('appointment_date')
            time_slot = request.POST.get('time_slot')
            symptoms = request.POST.get('symptoms')
            message = request.POST.get('message', '')
            
            if not appointment_date or not time_slot or not symptoms:
                messages.error(request, 'Please fill in all required fields')
                return redirect('doctors:book_appointments_by_search')
            
            # Convert time slot to time object
            time_slot_time = datetime.strptime(time_slot, '%H:%M').time()
            
            # Check if time slot is available (no existing appointments)
            is_booked = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=time_slot_time
            ).exists()
            
            if is_booked:
                messages.error(request, 'Selected time slot is already booked')
                return redirect('doctors:book_appointments_by_search')
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=request.user.patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=time_slot_time,
                symptoms=symptoms,
                message=message,
                status='pending'
            )
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('patients:view_appointments')
            
        except Doctor.DoesNotExist:
            messages.error(request, 'Doctor not found')
            return redirect('doctors:book_appointments_by_search')
        except ValueError:
            messages.error(request, 'Invalid time format')
            return redirect('doctors:book_appointments_by_search')
            
    return render(request, 'doctors/book_appointment_by_search.html', {
        'doctors': [],
        'search_query': ''
    })

@login_required
def doctor_dashboard(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
        
        # Get pending appointments
        pending_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='pending'
        ).order_by('appointment_date', 'appointment_time')
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='approved',
            appointment_date__gte=datetime.now().date()
        ).order_by('appointment_date', 'appointment_time')
        
        return render(request, 'doctors/dashboard.html', {
            'pending_appointments': pending_appointments,
            'upcoming_appointments': upcoming_appointments
        })
        
    except Doctor.DoesNotExist:
        messages.error(request, 'Access denied')
        return redirect('doctors:profile_setup')

@login_required
def approve_appointment(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id, doctor=request.user.doctor)
        appointment.status = 'approved'
        appointment.save()
        
        # Send email notification
        send_appointment_approval_email(appointment)
        
        messages.success(request, 'Appointment approved successfully!')
        return redirect('doctors:manage_appointments')
        
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found')
        return redirect('doctors:manage_appointments')

@login_required
def video_consultation(request, appointment_id):
    try:
        appointment = Appointment.objects.get(
            id=appointment_id,
            doctor=request.user.doctor,
            status='approved'
        )
        
        # Check if the appointment is within the consultation window
        current_time = datetime.now()
        consultation_window = timedelta(minutes=30)  # 30-minute consultation window
        
        appointment_datetime = datetime.combine(
            appointment.appointment_date,
            appointment.appointment_time
        )
        
        if current_time < appointment_datetime - consultation_window:
            messages.error(request, 'Consultation has not started yet')
            return redirect('doctors:manage_appointments')
        
        if current_time > appointment_datetime + consultation_window:
            messages.error(request, 'Consultation time has passed')
            return redirect('doctors:manage_appointments')
        
        return render(request, 'doctors/video_consultation.html', {
            'appointment': appointment
        })
        
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found or not approved')
        return redirect('doctors:manage_appointments')