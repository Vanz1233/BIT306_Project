from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class NGO(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Activity(models.Model):
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE, related_name='activities')
    service_type = models.CharField(max_length=100)
    event_date = models.DateField()
    start_time = models.TimeField()
    
    max_employees = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of volunteer slots"
    )
    cutoff_date = models.DateTimeField(help_text="Last date/time for employees to register")
    created_at = models.DateTimeField(auto_now_add=True)

    # --- MICROSERVICE SURGERY ---
    # We can no longer look up the Registration table. 
    # Instead, we store the count directly on the Activity.
    seats_taken = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        if self.cutoff_date and self.event_date:
            if self.cutoff_date.date() > self.event_date:
                raise ValidationError({
                    'cutoff_date': 'The cut-off date cannot be set after the actual event date.'
                })

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def seats_available(self):
        # Calculates based on the new integer field
        return self.max_employees - self.seats_taken

    def __str__(self):
        return f"{self.service_type} at {self.ngo.name}"
