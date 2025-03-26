from django.shortcuts import render, redirect
from .models import MedicalStore

def medical_store_profile_setup(request):
    if request.method == "POST":
        ms_name = request.POST['ms_name']
        ms_address = request.POST['ms_address']
        
        store = MedicalStore(user=request.user, ms_name=ms_name, ms_address=ms_address)
        store.save()

        request.user.profile_completed = True
        request.user.save()
        
        return redirect("medical_store_dashboard")
    return render(request, "medical_store/profile_setup.html")


def medical_store_dashboard(request):
    if not request.user.profile_completed:
        return redirect("profile_setup")
    return render(request, "medical_store/dashboard.html")