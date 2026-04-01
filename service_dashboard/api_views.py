from rest_framework import viewsets
from .models import NGO, Activity, Registration
from .serializers import NGOSerializer, ActivitySerializer, RegistrationSerializer

# Topic 8.1.a: NGO Management API
class NGOViewSet(viewsets.ModelViewSet):
    """Handles GET, POST, PUT, DELETE for NGOs"""
    queryset = NGO.objects.all()
    serializer_class = NGOSerializer
    
    # Topic 8.3.d: Filtering
    filterset_fields = ['location'] 
    search_fields = ['name']

# Topic 8.1.b: Activity Listing API
class ActivityViewSet(viewsets.ModelViewSet):
    """Handles GET, POST, PUT, DELETE for Activities"""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    
    # Topic 8.3.d: Filtering
    filterset_fields = ['event_date', 'ngo'] 

# Topic 8.1.c & d: Registration & Cancellation API
class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    
    def perform_create(self, serializer):
        # Automatically attach the logged-in user to the registration
        serializer.save(employee=self.request.user)