import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages

@csrf_exempt
def route_request(request, path):
    # The map of our Microservices
    SERVICES = {
        'users': 'http://127.0.0.1:8001',
        'ngos': 'http://127.0.0.1:8002',
        'registrations': 'http://127.0.0.1:8003',
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
# ... (Keep your other imports and route_request at the top)

def frontend_dashboard(request):
    activities = []
    try:
        response = requests.get('http://127.0.0.1:8002/api/ngos/activities/')
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
        
        # ... (keep the rest of your Port 8003 registration logic exactly as is) ...
        
        # --- NEW: Ask Port 8003 what this user is registered for ---
        try:
            reg_resp = requests.get('http://127.0.0.1:8003/api/registrations/list/', timeout=2)
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

    context = {
        'activities': activities,
        'now': timezone.now(),
        'user': mock_user, 
        'user_registered_ids': user_registered_ids, # Now the HTML knows what to hide!
        'is_admin_user': is_admin, 
    }
    return render(request, 'service_dashboard/index.html', context)


# --- NEW: The Secure Button Handler ---
def gateway_toggle_registration(request):
    """Securely grabs the session ID and sends the registration to Port 8003."""
    if request.method == 'POST':
        user_data = request.session.get('user_data')
        
        if not user_data:
            messages.error(request, "Security Error: You must be logged in to do that.")
            return redirect('dashboard')

        activity_id = request.POST.get('activity_id')
        action = request.POST.get('action') # Will be 'REGISTER' or 'WITHDRAW'

        try:
            # Forward the secure package to Port 8003
            response = requests.post('http://127.0.0.1:8003/api/registrations/toggle/', json={
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

def frontend_login(request):
    """Takes the HTML form and asks Port 8001 to verify it."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Send the credentials to our Security Guard (Port 8001)
            response = requests.post('http://127.0.0.1:8001/api/users/verify/', json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                # Passwords match! Save the user data into the Gateway's session.
                request.session['user_data'] = response.json()
                messages.success(request, "Login successful!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        except requests.exceptions.ConnectionError:
            messages.error(request, "User Service is currently down! Cannot login.")
            
    # If they just click "Login", show them your old login HTML page
    return render(request, 'accounts/login.html') 


def frontend_logout(request):
    """Destroys the session cookie."""
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('dashboard')
    
    
