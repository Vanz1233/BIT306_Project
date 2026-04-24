
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect

def sso_bridge(request, username):
    """Instantly logs the user into Port 8001 and forwards them to the requested page."""
    try:
        user = User.objects.get(username=username)
        login(request, user)
        
        # Grab the '?next=' parameter from the URL to know which page to load
        next_url = request.GET.get('next', '/admin/')
        return redirect(next_url)
        
    except User.DoesNotExist:
        return redirect('/admin/login/')
    
urlpatterns = [
    path('sso/<str:username>/', sso_bridge),
    path('admin/', admin.site.urls),
    path('api/users/', include('accounts.urls')),  # Include the accounts app URLs
]
