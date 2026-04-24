from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import time

# --- TOPIC 10.3: IMPORTS FOR CHANNELS ---
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Dynamically import the Registration model
try:
    from .models import Registration
except ImportError:
    from events.models import Registration

# ==========================================
# 1. THE RETRY MECHANISM (Topic 10 Excellent Tier)
# ==========================================
# bind=True and max_retries=3 allows the task to call itself again if it fails
@shared_task(bind=True, max_retries=3)
def send_registration_email(self, user_email, activity_name, ngo_name):
    try:
        # Simulate slow email
        time.sleep(3) 
        
        subject = f'Registration Confirmed: {activity_name}'
        message = f'Hi there!\n\nYou have successfully registered for {activity_name} hosted by {ngo_name}. We look forward to seeing you!\n\nBest,\nAuraIT CSR Team'
        email_from = 'YOUR_EMAIL@gmail.com' # Or no-reply@aurait-csr.com 
        recipient_list = [user_email]
        
        send_mail(subject, message, email_from, recipient_list)
        
        # TOPIC 10.3: REAL-TIME WEBSOCKET BROADCAST
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications",
            {
                "type": "send_notification",
                "message": {
                    "status": f"Registration Confirmed: Your spot for {activity_name} is secured. A confirmation email has been sent to your inbox."
                }
            }
        )
        
        return f"Success: Email sent to {user_email}"
        
    except Exception as exc:
        # If the email server crashes, wait 10 seconds and automatically try again
        raise self.retry(exc=exc, countdown=10)


# ==========================================
# 2. THE SCHEDULED REMINDER (Topic 10 Excellent Tier)
# ==========================================
@shared_task
def send_daily_reminders():
    """
    Finds all registrations for events happening TOMORROW and sends a reminder.
    """
    # Calculate exactly what date tomorrow is
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Query the database for any registrations where the activity is tomorrow
    upcoming_registrations = Registration.objects.filter(activity__event_date=tomorrow)
    
    count = 0
    for reg in upcoming_registrations:
        if reg.employee.email:
            subject = f'REMINDER: {reg.activity.service_type} is Tomorrow!'
            message = f'Hi {reg.employee.username},\n\nJust a friendly reminder that you are volunteering for {reg.activity.service_type} tomorrow at {reg.activity.start_time}.\n\nSee you there!\n\nAuraIT CSR Team'
            
            send_mail(subject, message, 'YOUR_EMAIL@gmail.com', [reg.employee.email])
            count += 1
            
    return f"Scheduled Task Complete: Sent {count} reminders for tomorrow's events."