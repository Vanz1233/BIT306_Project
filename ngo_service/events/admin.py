from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
import requests

from .models import NGO, Activity

# ==========================================
# 1. RESTORED MODEL ADMINS (From Monolith)
# ==========================================
@admin.register(NGO)
class NGOAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    search_fields = ('name', 'location')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'ngo', 'event_date', 'max_employees', 'seats_taken', 'seats_available')
    list_filter = ('event_date', 'ngo')
    search_fields = ('service_type', 'ngo__name')

    # --- MICROSERVICE BRIDGE FOR REGISTRATIONS ---
    # We attach custom URLs directly to the ActivityAdmin to handle the Port 8003 data
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('registrations-bridge/', self.admin_site.admin_view(self.registrations_bridge_view), name='events_activity_registrations_bridge'),
            path('registrations-bridge/delete/<int:activity_id>/<int:employee_id>/', self.admin_site.admin_view(self.registrations_delete_bridge), name='events_activity_registrations_delete'),
        ]
        return custom_urls + urls

    def registrations_bridge_view(self, request):
        """Fetches the registration list from Port 8003 and displays it in an Admin table"""
        registrations = []
        try:
            # Pick up the phone and call Port 8003
            response = requests.get('http://127.0.0.1:8003/api/registrations/stats/', timeout=2)
            if response.status_code == 200:
                registrations = response.json().get('registrations', [])
        except requests.RequestException:
            messages.error(request, "Could not connect to Registration Service (Port 8003).")

        # Map Activity IDs to actual names so the table is readable
        activity_map = {a.id: a.service_type for a in Activity.objects.all()}
        for reg in registrations:
            reg['activity_name'] = activity_map.get(reg['activity_id'], f"Event #{reg['activity_id']}")

        context = dict(
            self.admin_site.each_context(request),
            title="Registrations (Live from Port 8003)",
            registrations=registrations,
        )
        return render(request, 'admin/registrations_bridge.html', context)

    def registrations_delete_bridge(self, request, activity_id, employee_id):
        """Forwards the Delete action to Port 8003"""
        try:
            # Send a POST to Port 8003 to withdraw the user
            response = requests.post('http://127.0.0.1:8003/api/registrations/create/', json={
                'employee_id': employee_id,
                'activity_id': activity_id,
                'action': 'WITHDRAW'
            }, timeout=2)
            
            if response.status_code == 200:
                messages.success(request, "Registration successfully removed!")
                
                # Update the local seat counter on Port 8002
                activity = Activity.objects.get(id=activity_id)
                activity.seats_taken = max(0, activity.seats_taken - 1)
                activity.save()
            else:
                messages.error(request, "Failed to delete registration on Port 8003.")
        except Exception as e:
            messages.error(request, f"Error communicating with microservice: {e}")
            
        return redirect('admin:events_activity_registrations_bridge')

# ==========================================
# 2. DASHBOARD HIJACK (From Microservice)
# ==========================================
original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    total_users = 0
    try:
        response = requests.get('http://127.0.0.1:8001/api/users/list/', timeout=2)
        if response.status_code == 200:
            total_users = len(response.json())
    except requests.exceptions.ConnectionError:
        pass

    events = Activity.objects.all()
    
    extra_context = extra_context or {}
    extra_context.update({
        'total_users': total_users,
        'active_events': events.filter(cutoff_date__gte=timezone.now()).count(),
        'total_events': events.count(),
        'total_capacity': sum([e.max_employees for e in events]),
        'upcoming_events': events.order_by('event_date')[:5],
    })
    
    return original_index(request, extra_context)

admin.site.index = custom_admin_index

# ==========================================
# 3. UNIVERSAL MICROSERVICE SIDEBAR
# ==========================================
original_get_app_list = admin.site.get_app_list

def universal_get_app_list(request, app_label=None):
    # If Django is asking for a specific app's internal breadcrumbs, let it act normally
    app_list = original_get_app_list(request, app_label)
    if app_label is not None:
        return app_list
        
    # Safely get the username for the SSO Bridge
    username = getattr(request.user, 'username', 'admin')
    
    # We build a brand new, pristine list from scratch to prevent ANY duplicates
    clean_list = [
        {
            'name': 'Public Portal',
            'app_label': 'frontend',
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '🌐 View Employee Dashboard',
                    'object_name': 'dashboard',
                    'admin_url': 'http://127.0.0.1:8000/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'NGO Management',
            'app_label': 'events', 
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📅 Activities',
                    'object_name': 'activity',
                    'admin_url': 'http://127.0.0.1:8002/admin/events/activity/', 
                    'view_only': True,
                },
                {
                    'name': '🏢 NGOs',
                    'object_name': 'ngo',
                    'admin_url': 'http://127.0.0.1:8002/admin/events/ngo/', 
                    'view_only': True,
                },
                {
                    'name': '📋 Registrations (Live Data)',
                    'object_name': 'registration',
                    'admin_url': 'http://127.0.0.1:8002/admin/events/registration/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'User Management (RBAC)',
            'app_label': 'auth', 
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '👥 Manage Groups',
                    'object_name': 'group',
                    'admin_url': f'http://127.0.0.1:8001/sso/{username}/?next=/admin/auth/group/', 
                    'view_only': True,
                },
                {
                    'name': '👤 Manage Users',
                    'object_name': 'user',
                    'admin_url': f'http://127.0.0.1:8001/sso/{username}/?next=/admin/auth/user/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'CSR Operations',
            'app_label': 'csr',
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📸 Scan Ticket',
                    'object_name': 'scanner',
                    'admin_url': 'http://127.0.0.1:8002/admin/scanner/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'Broadcasts Management',
            'app_label': 'notifications',
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📢 Broadcast Center',
                    'object_name': 'broadcasts',
                    'admin_url': 'http://127.0.0.1:8002/admin/notifications/', 
                    'view_only': True,
                }
            ]
        }
    ]
    
    return clean_list

# ==========================================
# 3. UNIVERSAL MICROSERVICE SIDEBAR (Final Bulletproof Version)
# ==========================================
original_get_app_list = admin.site.get_app_list

def universal_get_app_list(request, app_label=None):
    if app_label is not None:
        return original_get_app_list(request, app_label)
        
    username = getattr(request.user, 'username', 'admin')
    
    clean_list = [
        {
            'name': 'Public Portal',
            'app_label': 'admin',  # Hooked into standard Django app to bypass security blocks
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '🌐 View Employee Dashboard',
                    'object_name': 'dashboard',
                    'admin_url': 'http://127.0.0.1:8000/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'NGO Management',
            'app_label': 'events', 
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📅 Activities',
                    'object_name': 'activity',
                    'admin_url': 'http://127.0.0.1:8002/admin/events/activity/', 
                    'view_only': True,
                },
                {
                    'name': '🏢 NGOs',
                    'object_name': 'ngo',
                    'admin_url': 'http://127.0.0.1:8002/admin/events/ngo/', 
                    'view_only': True,
                },
                {
                    'name': '📋 Registrations (Live Data)',
                    'object_name': 'registration',
                    'admin_url': '/admin/events/activity/registrations-bridge/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'User Management (RBAC)',
            'app_label': 'auth',  
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '👥 Manage Groups',
                    'object_name': 'group',
                    'admin_url': f'http://127.0.0.1:8001/sso/{username}/?next=/admin/auth/group/', 
                    'view_only': True,
                },
                {
                    'name': '👤 Manage Users',
                    'object_name': 'user',
                    'admin_url': f'http://127.0.0.1:8001/sso/{username}/?next=/admin/auth/user/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'CSR Operations',
            'app_label': 'sessions', # Hooked into standard Django app
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📸 Scan Ticket',
                    'object_name': 'scanner',
                    'admin_url': 'http://127.0.0.1:8002/admin/scanner/', 
                    'view_only': True,
                }
            ]
        },
        {
            'name': 'Broadcasts Management',
            'app_label': 'contenttypes', # Hooked into standard Django app
            'app_url': '',
            'has_module_perms': True,
            'models': [
                {
                    'name': '📢 Broadcast Center',
                    'object_name': 'broadcasts',
                    'admin_url': 'http://127.0.0.1:8002/admin/notifications/', 
                    'view_only': True,
                }
            ]
        }
    ]
    
    return clean_list

admin.site.get_app_list = universal_get_app_list