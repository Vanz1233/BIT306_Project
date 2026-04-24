from django.db import models

class Registration(models.Model):
    # --- MICROSERVICE SURGERY ---
    # No more ForeignKeys! These are now just simple numbers.
    # The API Gateway will pass these numbers in when a user clicks "Register".
    employee_id = models.IntegerField(help_text="ID of the User from Port 8001")
    activity_id = models.IntegerField(help_text="ID of the Activity from Port 8002")
    
    # We add a status field so the "Withdraw" button can easily cancel a registration
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('ATTENDED', 'Attended'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # We still want to prevent double-booking using the new ID fields
        unique_together = ('employee_id', 'activity_id')

    def __str__(self):
        # We can't do self.employee.username anymore because the User table isn't here!
        return f"User ID: {self.employee_id} -> Activity ID: {self.activity_id} [{self.status}]"
