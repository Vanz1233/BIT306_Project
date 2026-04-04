from celery import shared_task
from django.core.mail import send_mail
import time

@shared_task
def send_registration_email(user_email, activity_name, ngo_name):
    """
    Topic 10.2: Background job to send email reminders.
    This runs completely independent of the main Django server!
    """
    # We add a 3-second sleep to simulate a slow email server.
    # If this wasn't asynchronous, the user's web page would freeze for 3 seconds!
    time.sleep(3) 
    
    subject = f'Registration Confirmed: {activity_name}'
    message = f'Hi there!\n\nYou have successfully registered for {activity_name} hosted by {ngo_name}. We look forward to seeing you!\n\nBest,\nAuraIT CSR Team'
    email_from = 'no-reply@aurait-csr.com'
    recipient_list = [user_email]
    
    send_mail(subject, message, email_from, recipient_list)
    return f"Success: Email sent to {user_email}"