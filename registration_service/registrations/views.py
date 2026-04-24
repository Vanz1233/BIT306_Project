from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Registration
from .serializers import RegistrationSerializer
import requests  # <-- NEW: Imported requests for the microservice ping

class RegistrationCreateView(generics.CreateAPIView):
    """API Endpoint to allow an employee to register or withdraw"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        employee_id = request.data.get('employee_id')
        activity_id = request.data.get('activity_id')
        action = request.data.get('action', 'REGISTER')

        if not employee_id or not activity_id:
            return Response({'error': 'Missing employee_id or activity_id'}, status=status.HTTP_400_BAD_REQUEST)

        # Find the existing receipt, or create a brand new one
        registration, created = Registration.objects.get_or_create(
            employee_id=employee_id,
            activity_id=activity_id
        )

        # Update the status based on the button they clicked
        if action == 'REGISTER':
            registration.status = 'REGISTERED'
            message = "Successfully registered for the event!"
        elif action == 'WITHDRAW':
            registration.status = 'CANCELLED'
            message = "Successfully withdrew from the event."
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        registration.save()

        # --- NEW: THE MICROSERVICE PING ---
        # Throw the paper airplane to Port 8002 to update its integer field!
        try:
            requests.post('http://127.0.0.1:8002/api/events/update-seats/', json={
                'activity_id': activity_id,
                'action': action
            }, timeout=2)
        except requests.exceptions.RequestException:
            print("Warning: Could not reach Port 8002 to update the seat counter.")

        return Response({
            'message': message, 
            'status': registration.status,
            'activity_id': activity_id
        }, status=status.HTTP_200_OK)


class RegistrationListView(generics.ListAPIView):
    """API Endpoint to see all registrations"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer


class RegistrationStatsView(APIView):
    """Provides raw sign-up data to power the Admin Dashboard chart."""
    def get(self, request):
        active_regs = Registration.objects.filter(status='REGISTERED')
        
        data = [
            {
                'employee_id': reg.employee_id,
                'activity_id': reg.activity_id,
                'registered_at': reg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for reg in active_regs
        ]
        
        return Response({'total_active': active_regs.count(), 'registrations': data}, status=status.HTTP_200_OK)
