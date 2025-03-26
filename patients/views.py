from django.shortcuts import render, redirect
from .models import Patient
from django.contrib import messages
from datetime import datetime

def patient_profile_setup(request):
    if request.method == "POST":
        try:
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
            
            # Validate age (should be reasonable)
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
            
            return redirect("patient_dashboard")
            
        except KeyError as e:
            messages.error(request, f"Missing required field: {str(e)}")
            return render(request, "patients/profile_setup.html")
        except ValueError:
            messages.error(request, "Please enter a valid date format (YYYY-MM-DD)")
            return render(request, "patients/profile_setup.html")
            
    return render(request, "patients/profile_setup.html")

def patient_dashboard(request):
    if not request.user.profile_completed:
        return redirect("profile_setup")
    return render(request, "patients/dashboard.html")


def patient_profile(request):
    if not request.user.profile_completed:
        return redirect("profile_setup")
    return render(request, "patients/profile.html")