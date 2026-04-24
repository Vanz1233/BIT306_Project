from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect

def sso_bridge(request, username):
    """A local bridge to instantly log in users arriving from the Gateway."""
    try:
        # 1. Find the user in Port 8002's local database
        user = User.objects.get(username=username)
        
        # 2. Force Django to log them into the session
        login(request, user)
        
        # 3. Teleport them straight into the dashboard!
        return redirect('/admin/')
    except User.DoesNotExist:
        # If the user doesn't exist on Port 8002, kick them to the login screen
        return redirect('/admin/login/')

urlpatterns = [
    path('admin/logout/', LogoutView.as_view(next_page='http://127.0.0.1:8000/logout/')),
    path('sso/<str:username>/', sso_bridge),
    path('admin/', admin.site.urls),
    path('api/ngos/', include('events.urls')),
]
