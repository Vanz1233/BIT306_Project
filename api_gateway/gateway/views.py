import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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
