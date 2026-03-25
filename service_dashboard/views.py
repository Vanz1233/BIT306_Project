from django.shortcuts import render, get_object_or_404, redirect  
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import NGO, Activity, Registration
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.contrib import messages, admin  
from .services import EventService   
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

# --- Helper Check (UPDATED FOR TOPIC 6 RBAC) ---
def is_admin(user):
    """
    Topic 6.4: Role-Based Access Control.
    Checks if the user is a superuser OR belongs to the 'Admin Group'.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name='Admin Group').exists()

# --- Main Views ---
def dashboard(request):
    """
    The main landing page. 
    It aggregates data but doesn't handle the 'heavy lifting' of registration logic.
    """
    # --- UPDATED: TASK 5.4.b.i select_related() ---
    # Fetches the linked NGO in the same query to prevent N+1 performance issues
    activities = Activity.objects.select_related('ngo').all()
    
    user_registered_ids = []
    
    if request.user.is_authenticated:
        user_registered_ids = Registration.objects.filter(employee=request.user).values_list('activity_id', flat=True)

    return render(request, 'service_dashboard/index.html', {
        'activities': activities,
        'user_registered_ids': user_registered_ids,
        'now': timezone.now(),
        'is_admin_user': is_admin(request.user) if request.user.is_authenticated else False, # <-- ADD THIS LINE
    })

# --- Admin Views ---
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # 1. Grab native Django context 
    context = admin.site.each_context(request)
    app_list = admin.site.get_app_list(request)
            
    context['available_apps'] = app_list
    
    # 2. Add our custom stats
    total_users = User.objects.count()
    
    total_events = Activity.objects.count() 
    
    active_events_count = Activity.objects.annotate(
        booked_count=Count('registration')
    ).filter(
        booked_count__lt=F('max_employees'), 
        cutoff_date__gt=timezone.now()
    ).count()

    # --- UPDATED: TASK 5.4.b select_related() AND prefetch_related() ---
    upcoming_events = Activity.objects.select_related('ngo').prefetch_related(
        'registration_set'
    ).filter(
        event_date__gte=timezone.now()
    ).order_by('event_date')[:5]

    # --- NEW: TASK 5.2 .aggregate() DEMONSTRATION ---
    # Calculates the total number of volunteer slots across all activities
    capacity_data = Activity.objects.aggregate(total_slots=Sum('max_employees'))
    total_capacity = capacity_data['total_slots'] or 0

    # 3. Merge them together
    context.update({
        'total_users': total_users,
        'total_events': total_events,
        'active_events': active_events_count,
        'upcoming_events': upcoming_events,
        'total_capacity': total_capacity,
    })
    
    return render(request, 'service_dashboard/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def scanner_prototype(request):
    """Admin view to simulate scanning a QR code (Use Case 6)"""
    context = admin.site.each_context(request)

    if request.method == 'POST':
        attendee = request.POST.get('attendee_name')
        messages.success(request, f"SCAN SUCCESS: {attendee} has been successfully checked in!")
        return redirect('scanner_prototype') 
        
    return render(request, 'service_dashboard/scanner.html', context)
# --- Employee Ticket View ---
@login_required
def view_ticket(request, event_id):
    """Employee view to see their own QR code ticket (Use Case 6)"""
    event = get_object_or_404(Activity, id=event_id)
    
    context = {
        'event': event,
        'user': request.user
    }
    return render(request, 'service_dashboard/ticket.html', context)

@login_required
def register_event(request, activity_id):
    if request.method == 'POST':
        # Delegate to Service Layer
        success, message = EventService.register_employee(request.user, activity_id)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    return redirect('dashboard')

@require_http_methods(["DELETE"])
@login_required
def cancel_registration(request, activity_id):
    """
    Topic 3.1d: Uses proper DELETE HTTP method for cancellations.
    """
    # Delegate to Service Layer
    success, message = EventService.withdraw_employee(request.user, activity_id)
    
    if success:
        return JsonResponse({"status": "success", "message": message})
    else:
        return JsonResponse({"status": "error", "message": message}, status=400)

@login_required
def smart_login_redirect(request):
    """
    Acts as a traffic cop after login.
    """
    if request.user.is_superuser or request.user.is_staff:
        return redirect('/admin/')
    else:
        return redirect('/')
    
# ==========================================
# TRAFFIC COP (Smart Login Redirect)
# ==========================================
def smart_redirect(request):
    """Routes users to the correct dashboard based on their role after login."""
    if is_admin(request.user):
        return redirect('/admin/') # Sends Admins straight to the backend
    else:
        return redirect('dashboard') # Sends Employees to the frontend




