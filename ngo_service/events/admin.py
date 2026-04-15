from django.contrib import admin
import requests
from django.utils import timezone
from .models import NGO, Activity

# Register your models
admin.site.register(NGO)
admin.site.register(Activity)

# Hijack the default admin index view to inject our Microservice stats!
original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    # 1. Ask User Service (Port 8001) for the actual user count!
    total_users = 0
    try:
        # Assuming you have a list view at /api/users/list/
        response = requests.get('http://127.0.0.1:8001/api/users/list/', timeout=2)
        if response.status_code == 200:
            total_users = len(response.json())
    except requests.exceptions.ConnectionError:
        print("Could not reach User Service for staff count.")

    # 2. Get local database stats from Port 8002
    events = Activity.objects.all()
    
    extra_context = extra_context or {}
    extra_context.update({
        'total_users': total_users,  # Now this is completely dynamic!
        'active_events': events.filter(cutoff_date__gte=timezone.now()).count(),
        'total_events': events.count(),
        'total_capacity': sum([e.max_employees for e in events]),
        'upcoming_events': events.order_by('event_date')[:5],
    })
    
    return original_index(request, extra_context)

# Apply the hijack
admin.site.index = custom_admin_index
