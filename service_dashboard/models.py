from django.db import models
from django.contrib.auth.models import User 
from django.core.validators import MinValueValidator

# --- NEW: Imported ValidationError for Task 5.3 ---
from django.core.exceptions import ValidationError

class NGO(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    
    # NEW: 5.1 Timestamp requirement
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'NGO'
        verbose_name_plural = 'NGOs'

class Activity(models.Model):
    # NEW: 5.1 Foreign Key mapping linking Activity to NGO
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE, related_name='activities')
    
    service_type = models.CharField(max_length=100)
    event_date = models.DateField()
    start_time = models.TimeField()
    
    # UPDATED: 5.1 Field validation (MinValueValidator)
    max_employees = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of volunteer slots"
    )
    cutoff_date = models.DateTimeField(help_text="Last date/time for employees to register")
    
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NEW: TASK 5.3 Custom Model & Form Validation ---
    def clean(self):
        super().clean()
        # Rule: Cut-off date cannot be after the event date
        if self.cutoff_date and self.event_date:
            # We use .date() to compare the DateTimeField to the DateField
            if self.cutoff_date.date() > self.event_date:
                raise ValidationError({
                    'cutoff_date': 'The cut-off date cannot be set after the actual event date.'
                })

    def save(self, *args, **kwargs):
        self.full_clean() # Forces the clean() method to run before saving to the database
        super().save(*args, **kwargs)

    def seats_taken(self):
        return self.registration_set.count()

    def seats_available(self):
        return self.max_employees - self.seats_taken()

    def __str__(self):
        return f"{self.service_type} at {self.ngo.name}"
        
    class Meta:
        verbose_name = 'Event'          
        verbose_name_plural = 'Events'  

class Registration(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # UPDATED: Registration now links to the Activity, not the NGO directly
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)
    
    # UPDATED: Renamed from 'registered_at' to 'created_at' to strictly match 5.1 wording
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents an employee from registering for the same activity twice
        unique_together = ('employee', 'activity')

    def __str__(self):
        return f"{self.employee.username} - {self.activity.service_type}"
    

