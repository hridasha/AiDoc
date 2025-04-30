from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_appointment_approval_email(appointment):
    subject = f'Appointment Approved - {appointment.doctor.full_name}'
    to_email = appointment.patient.user.email
    
    # Render the email template
    context = {
        'appointment': appointment,
        'doctor': appointment.doctor,
        'patient': appointment.patient
    }
    
    html_message = render_to_string('emails/appointment_approved.html', context)
    text_message = render_to_string('emails/appointment_approved.txt', context)
    
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_email],
        html_message=html_message
    )