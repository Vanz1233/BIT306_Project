from django.shortcuts import render, redirect
from django.contrib import messages, admin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Notification

from rest_framework import generics
import json

from .models import NGO, Activity
from .serializers import NGOSerializer, ActivitySerializer

# ==========================================
# 1. MICROSERVICE RBAC & SCANNER (Admin UI)
# ==========================================
def is_admin(user):
    """Checks if the user has the Admin badge from Port 8001"""
    if user.is_superuser:
        return True
    return user.groups.filter(name='Admin Group').exists()

@login_required
def scanner_prototype(request):
    """Admin view to simulate scanning a QR code"""
    # Security: Kick out unauthorized users
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to access the scanner.")
        return redirect('/')

    # This pulls in the Jazzmin sidebar and header so the page doesn't look broken
    context = admin.site.each_context(request)
    context['title'] = "CSR Ticket Scanner"

    # Handle the mock check-in from the HTML button
    if request.method == 'POST':
        attendee = request.POST.get('attendee_name', 'Mock Attendee')
        messages.success(request, f"SCAN SUCCESS: {attendee} has been successfully checked in!")
        return redirect('scanner_prototype') 
        
    return render(request, 'admin/scanner.html', context)

# ==========================================
# 2. REST API & MICROSERVICE WEBHOOKS
# ==========================================
@csrf_exempt
def update_seat_count(request):
    """Receives the ping from Port 8003 to update the seats_taken counter."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activity_id = data.get('activity_id')
            action = data.get('action') # 'REGISTER' or 'WITHDRAW'

            activity = Activity.objects.get(id=activity_id)
            
            if action == 'REGISTER':
                activity.seats_taken += 1
            elif action == 'WITHDRAW':
                # max(0, ...) ensures we never accidentally go into negative numbers
                activity.seats_taken = max(0, activity.seats_taken - 1)
                
            activity.save()
            return JsonResponse({'status': 'success', 'seats_taken': activity.seats_taken})
        
        except Activity.DoesNotExist:
            return JsonResponse({'error': 'Activity not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)

class NGOListView(generics.ListCreateAPIView):
    """Returns a JSON list of all NGOs"""
    queryset = NGO.objects.all()
    serializer_class = NGOSerializer

class ActivityListView(generics.ListCreateAPIView):
    """Returns a JSON list of all Activities"""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

class ActivityDetailView(generics.RetrieveUpdateAPIView):
    """Returns JSON details for a single specific activity"""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

@login_required
def admin_notification_panel(request):
    """Admin view to broadcast messages"""
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to access the Broadcast Center.")
        return redirect('/')

    events = NGO.objects.all()
    context = admin.site.each_context(request)
    context['events'] = events
    context['title'] = "Broadcast Center"

    if request.method == 'POST':
        if 'broadcast' in request.POST:
            title = request.POST.get('subject')
            body = request.POST.get('message')
            
            # Note: In a full microservice, you would ping Port 8001 via API here.
            # For the prototype, we replicate your monolith's local DB behavior.
            recipients = User.objects.all()
            for user in recipients:
                Notification.objects.create(recipient=user, title=title, message=body)
                
            messages.success(request, f"Broadcast sent successfully across the network!")
            return redirect('admin_notification_panel')
            
    return render(request, 'admin/broadcast_panel.html', context)

# --- Add to the bottom of ngo_service/events/views.py ---
@csrf_exempt
def api_user_notifications(request, username):
    """API endpoint for Port 8000 to fetch a user's notifications."""
    try:
        # Find the user and their notifications
        user = User.objects.get(username=username)
        notifs = Notification.objects.filter(recipient=user).order_by('-created_at')
        
        # Package them into JSON
        data = []
        for n in notifs:
            data.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'created_at': n.created_at.strftime("%Y-%m-%d %H:%M"),
                'is_read': n.is_read
            })
        
        # Mark them as read automatically once fetched
        notifs.filter(is_read=False).update(is_read=True)
        
        return JsonResponse({'notifications': data})
    except User.DoesNotExist:
        return JsonResponse({'notifications': []})