from rest_framework import generics
from .models import Registration
from .serializers import RegistrationSerializer

class RegistrationCreateView(generics.CreateAPIView):
    """API Endpoint to allow an employee to register for an event"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer

class RegistrationListView(generics.ListAPIView):
    """API Endpoint to see all registrations"""
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
