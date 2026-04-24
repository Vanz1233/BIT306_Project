from rest_framework import generics
from .models import NGO, Activity
from .serializers import NGOSerializer, ActivitySerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Activity

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
