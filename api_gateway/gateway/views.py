import os
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages

# ==========================================
# MICROSERVICE CLOUD ROUTING VARIABLES
# ==========================================
# Grabs the Render URLs if they exist. Defaults to your laptop if they don't!
# rstrip('/') ensures we don't accidentally create double-slashes in our URLs.
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://127.0.0.1:8001').rstrip('/')
NGO_SERVICE_URL = os.environ.get('NGO_SERVICE_URL', 'http://127.0.0.1:8002').rstrip('/')
REGISTRATION_SERVICE_URL = os.environ.get('REGISTRATION_SERVICE_URL', 'http://127.0.0.1:8003').rstrip('/')

@csrf_exempt
def route_request(request, path):
    # The map of our Microservices using our new Cloud Variables
    SERVICES = {
        'users': USER_SERVICE_URL,
        'ngos': NGO_SERVICE_URL,
        'registrations': REGISTRATION_SERVICE_URL,
    }

    # Figure out which service they want (e.g., 'ngos' from 'ngos/activities/')
    service_name = path.split('/')[0]

    if service_name not in SERVICES:
        return JsonResponse({'error': 'Service not found in Gateway'}, status=404)

    # Build the exact URL for the target microservice
    target_url = f"{SERVICES[service_name]}/api/{path}"

    try:
        # Forward a GET request
        if request.method == 'GET':
            response = requests.get(target_url, params=request.GET)
            
        # Forward a POST request
        elif request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            response = requests.post(target_url, json=data)
            
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        # Return the microservice's exact response back to the user
        try:
            return JsonResponse(response.json(), safe=False, status=response.status_code)
        except ValueError:
            return JsonResponse({'error': 'Microservice did not return JSON'}, status=500)

    except requests.exceptions.ConnectionError:
        return JsonResponse({'error': f'{service_name} microservice is currently down!'}, status=503)


# ==========================================
# FRONTEND VIEWS (The HTML Skin)
# ==========================================

def frontend_dashboard(request):
    activities = []
    try:
        response = requests.get(f'{NGO_SERVICE_URL}/api/ngos/activities/')
        if response.status_code == 200:
            activities = response.json()
    except requests.exceptions.ConnectionError:
        print("Warning: NGO Service is down!")

    user_data = request.session.get('user_data')
    user_registered_ids = [] 
    
    if user_data:
        # --- THE BULLETPROOF FIX ---
        # If the session still holds the old nested format, unpack it safely!
        if 'username' not in user_data and 'user_data' in user_data:
            user_data = user_data['user_data']
        # ---------------------------

        mock_user = {
            'is_authenticated': True,
            'username': user_data['username'],
            'first_name': user_data.get('first_name', ''),
            'id': user_data['id']
        }
        is_admin = user_data.get('is_staff', False)
        
        # --- Ask the Registration Service what this user is registered for ---
        try:
            reg_resp = requests.get(f'{REGISTRATION_SERVICE_URL}/api/registrations/list/', timeout=2)
            if reg_resp.status_code == 200:
                all_regs = reg_resp.json()
                # Filter out just the active activity IDs for this specific user
                user_registered_ids = [
                    r['activity_id'] for r in all_regs 
                    if r['employee_id'] == user_data['id'] and r['status'] == 'REGISTERED'
                ]
        except requests.exceptions.ConnectionError:
            print("Warning: Registration Service is down!")
            
    else:
        mock_user = {'is_authenticated': False}
        is_admin = False

    # ---> THE FIX IS RIGHT HERE! <---
    context = {
        'activities': activities,
        'now': timezone.now(),
        'user': mock_user, 
        'user_registered_ids': user_registered_ids, # Now the HTML knows what to hide!
        'is_admin_user': is_admin, 
        'ngo_service_url': NGO_SERVICE_URL, # We added this line to pass the cloud URL to HTML
    }
    return render(request, 'service_dashboard/index.html', context)


# --- Secure Button Handler ---
def gateway_toggle_registration(request):
    """Securely grabs the session ID and sends the registration to the Registration Service."""
    if request.method == 'POST':
        user_data = request.session.get('user_data')
        
        if not user_data:
            messages.error(request, "Security Error: You must be logged in to do that.")
            return redirect('dashboard')

        activity_id = request.POST.get('activity_id')
        action = request.POST.get('action') # Will be 'REGISTER' or 'WITHDRAW'

        try:
            # Forward the secure package to the Registration Service
            response = requests.post(f'{REGISTRATION_SERVICE_URL}/api/registrations/toggle/', json={
                'employee_id': user_data['id'],
                'activity_id': int(activity_id),
                'action': action
            })

            if response.status_code == 200:
                messages.success(request, response.json().get('message'))
            else:
                messages.error(request, "Failed to process registration.")
                
        except requests.exceptions.ConnectionError:
            messages.error(request, "Registration service is currently down!")

    return redirect('dashboard')


# --- NEW: User Notifications View ---
def user_notifications(request):
    """Fetches notifications from the NGO Service and renders them."""
    user_data = request.session.get('user_data')
    
    # Custom session check
    if not user_data:
        messages.error(request, "You must be logged in to view notifications.")
        return redirect('dashboard')
        
    # Unpack nested format if necessary
    if 'username' not in user_data and 'user_data' in user_data:
        user_data = user_data['user_data']

    username = user_data.get('username')
    notifications = []
    
    try:
        # Pick up the phone and call NGO Service API
        response = requests.get(f'{NGO_SERVICE_URL}/api/notifications/{username}/', timeout=2)
        if response.status_code == 200:
            notifications = response.json().get('notifications', [])
    except requests.exceptions.RequestException:
        messages.error(request, "Notification service is currently unreachable.")
        
    # Mock user object so the navbar still works in the template
    mock_user = {
        'is_authenticated': True,
        'username': username,
        'first_name': user_data.get('first_name', ''),
        'id': user_data.get('id')
    }

    return render(request, 'service_dashboard/notifications.html', {
        'notifications': notifications,
        'user': mock_user
    })

def frontend_login(request):
    """Takes the HTML form and asks the User Service to verify it."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Send the credentials to our Security Guard (User Service)
            response = requests.post(f'{USER_SERVICE_URL}/api/users/verify/', json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                request.session['user_data'] = response.json()
                messages.success(request, "Login successful!")
                return redirect('dashboard')
            else:
                # DIAGNOSTIC FIX: Show EXACTLY what the backend is saying!
                error_details = f"Backend Error {response.status_code}: {response.text}"
                messages.error(request, error_details)
                print(error_details) # Also prints to your Render logs
                
        except requests.exceptions.ConnectionError:
            messages.error(request, "User Service is currently down! Cannot login.")
            
    return render(request, 'accounts/login.html') 


def frontend_logout(request):
    """Destroys the session cookie."""
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('dashboard')
    
