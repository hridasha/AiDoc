from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from .models import CustomUser

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(f"User registered successfully: {user.username}")
            return redirect("user_login")
    else:
        form = RegisterForm()
    return render(request, "authentication/register.html", {"form": form})

def user_login(request):
    print("Login view called")
    if request.method == "POST":
        print("POST request received")
        form = LoginForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            print(f"Attempting to authenticate user: {username}")
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                print(f"User authenticated successfully: {user.username}")
                login(request, user)
                print(f"User logged in: {user.username}")
                print(f"User role: {user.role}")
                print(f"Profile completed: {user.profile_completed}")
                if user.profile_completed:
                    print("Redirecting to dashboard")
                    if user.role == 'patient':
                        return redirect('patients:dashboard')
                    elif user.role == 'doctor':
                        return redirect('doctors:doctor_dashboard')
                    elif user.role == 'medical_store':
                        return redirect('medical_store:dashboard')
                print("Redirecting to profile setup")
                if user.role == 'patient':
                    return redirect('patients:patient_profile_setup')
                elif user.role == 'doctor':
                    return redirect('doctors:profile_setup')
                elif user.role == 'medical_store':
                    return redirect('medical_store:profile_setup')
            else:
                print("Authentication failed")
                form.add_error(None, "Invalid username or password")
    else:
        print("GET request - showing login form")
        form = LoginForm()
    return render(request, "authentication/login.html", {"form": form})

def profile_setup(request):
    print("Profile setup view called")
    user = request.user
    print(f"Current user: {user.username if user.is_authenticated else 'Anonymous'}")
    print(f"User is authenticated: {user.is_authenticated}")
    print(f"User role: {user.role}")
    print(f"Profile completed: {user.profile_completed}")
    
    if user.is_authenticated:
        if user.profile_completed:
            print("Profile is completed, redirecting to dashboard")
            return redirect(f"{user.role}_dashboard")
        
        if user.role == "doctor":
            print("Doctor role detected, redirecting to doctor profile setup")
            return redirect("doctor_profile_setup")
        elif user.role == "patient":
            print("Patient role detected, redirecting to patient profile setup")
            return redirect("patient_profile_setup")
        elif user.role == "medical_store":
            print("Medical store role detected, redirecting to medical store profile setup")
            return redirect("medical_store_profile_setup")
        else:
            print("Invalid user role detected")
            return render(request, "authentication/profile_setup_error.html", {
                "error": "Invalid user role"
            })
    print("User not authenticated, redirecting to login")
    return redirect("user_login")

def user_logout(request):
    logout(request)
    return redirect("user_login")
