from django.db import transaction
from django.utils import timezone
from .models import NGO, Activity, Registration
from .tasks import send_registration_email

class EventService:
    """
    Handles business logic for Event Registration.
    Separates logic from the View layer (Topic 2.2).
    """

    @staticmethod
    def register_employee(user, activity_id):
        try:
            # Topic 4.5: Start the Atomic Transaction 
            with transaction.atomic():
                # 1. Fetch Data & Lock the Row (Topic 4.5)
                activity = Activity.objects.select_for_update().get(id=activity_id)
            
                # 2. Rule: Check Cut-off Date (Topic 2.2 - Validation)
                if timezone.now() > activity.cutoff_date:
                    return False, "Registration for this event has closed."

                # 3. Rule: Check Duplicate Registration
                if Registration.objects.filter(employee=user, activity=activity).exists():
                    return False, f"You are already registered for {activity.service_type}."

                # 4. Rule: Check Slot Availability (Topic 2.2 - Availability Checks)
                if activity.seats_available() <= 0:
                    return False, f"Sorry, {activity.service_type} is full."

                # 5. Execute Transaction
                Registration.objects.create(employee=user, activity=activity)
                
                # ==========================================
                # TOPIC 10.2: TRIGGER BACKGROUND EMAIL TASK
                # ==========================================
                # .delay() drops the job into Memurai so the user doesn't wait!
                if user.email: 
                    send_registration_email.delay(user.email, activity.service_type, activity.ngo.name)

                return True, f"Successfully registered for {activity.service_type} at {activity.ngo.name}!"

        except Activity.DoesNotExist:
            return False, "Event not found."
        except Exception as e:
            # If any database error occurs, the atomic block safely cancels everything
            return False, "An unexpected error occurred during registration."

    @staticmethod
    # UPDATED: Changed ngo_id to activity_id
    def withdraw_employee(user, activity_id):
        try:
            # UPDATED: Fetch Activity
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return False, "Event not found."

        # Rule: Cannot withdraw after cut-off
        if timezone.now() > activity.cutoff_date:
            return False, "It is too late to cancel your registration."

        # UPDATED: Check against activity
        registration = Registration.objects.filter(employee=user, activity=activity).first()
        if registration:
            registration.delete()
            return True, f"You have withdrawn from {activity.service_type}."
        else:
            return False, "You are not registered for this event."
        
    @staticmethod
    # UPDATED: Changed ngo_id to activity_id
    def get_ticket_verification(user, activity_id):
        """
        Service layer check to verify if an event exists and if the user is registered.
        """
        try:
            # UPDATED: Fetch Activity
            activity = Activity.objects.get(id=activity_id)
            is_registered = Registration.objects.filter(employee=user, activity=activity).exists()
            return activity, is_registered
        except Activity.DoesNotExist:
            return None, False