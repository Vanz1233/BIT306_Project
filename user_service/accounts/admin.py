import os
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ==========================================
# CLOUD ENVIRONMENT VARIABLES
# ==========================================
API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL', 'http://127.0.0.1:8000').rstrip('/')
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://127.0.0.1:8001').rstrip('/')
NGO_SERVICE_URL = os.environ.get('NGO_SERVICE_URL', 'http://127.0.0.1:8002').rstrip('/')
REGISTRATION_SERVICE_URL = os.environ.get('REGISTRATION_SERVICE_URL', 'http://127.0.0.1:8003').rstrip('/')

# 1. Unregister Django's default User admin
admin.site.unregister(User)

# 2. Inject your exact monolith logic
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        ('User Profile & Roles', {
            'fields': ('username', 'first_name', 'last_name', 'email', 'groups')
        }),
    )
    
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_filter = ()
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def has_delete_permission(self, request, obj=None):
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update({
            'show_save_and_continue': False,
            'show_save_and_add_another': False,
            'show_delete': False
        })
        return super().render_change_form(request, context, add, change, form_url, obj)

# 3. Register it back
admin.site.register(User, CustomUserAdmin)

# ==========================================
# UNIVERSAL MICROSERVICE SIDEBAR
# ==========================================
original_get_app_list = admin.site.get_app_list

def universal_get_app_list(request, app_label=None):
    # If Django is asking for a specific app's internal breadcrumbs, let it act normally
    if app_label is not None:
        return original_get_app_list(request, app_label)
        
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
                    'admin_url': f'{API_GATEWAY_URL}/', 
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
                    'admin_url': f'{NGO_SERVICE_URL}/admin/events/activity/', 
                    'view_only': True,
                },
                {
                    'name': '🏢 NGOs',
                    'object_name': 'ngo',
                    'admin_url': f'{NGO_SERVICE_URL}/admin/events/ngo/', 
                    'view_only': True,
                },
                {
                    'name': '📋 Registrations (Live Data)',
                    'object_name': 'registration',
                    'admin_url': f'{NGO_SERVICE_URL}/admin/events/activity/registrations-bridge/', 
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
                    'admin_url': '/admin/auth/group/', 
                    'view_only': True,
                },
                {
                    'name': '👤 Manage Users',
                    'object_name': 'user',
                    'admin_url': '/admin/auth/user/', 
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
                    'admin_url': f'{NGO_SERVICE_URL}/admin/scanner/', 
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
                    'admin_url': f'{NGO_SERVICE_URL}/admin/notifications/', 
                    'view_only': True,
                }
            ]
        }
    ]
    
    return clean_list

# Overwrite Django's default behavior globally
admin.site.get_app_list = universal_get_app_list
