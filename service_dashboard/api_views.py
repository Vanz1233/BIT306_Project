from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import NGO, Activity, Registration
from .serializers import NGOSerializer, ActivitySerializer, RegistrationSerializer

# ==========================================
# CUSTOM API PERMISSIONS (TOPIC 7.3)
# ==========================================
class IsAdminOrReadOnly(BasePermission):
    """Allows anyone to view, but only Admins can create/edit/delete NGOs and Activities."""
    def has_permission(self, request, view):
        # Allow GET requests for everyone
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # Require Admin status for POST/PUT/DELETE
        return request.user.is_superuser or request.user.groups.filter(name='Admin Group').exists()

class IsEmployeeOnly(BasePermission):
    """Only allows Employees to interact with this endpoint."""
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Employee Group').exists() and not request.user.is_superuser

# ==========================================
# API VIEWS (TOPIC 8)
# ==========================================

# Topic 8.1.a & 7.3.b: NGO Management API
class NGOViewSet(viewsets.ModelViewSet):
    """Handles GET, POST, PUT, DELETE for NGOs"""
    queryset = NGO.objects.all()
    serializer_class = NGOSerializer
    
    # Topic 8.3.d: Filtering
    filterset_fields = ['location'] 
    search_fields = ['name']
    
    # Topic 7.3.a & 7.3.b: Security
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly] 

# Topic 8.1.b: Activity Listing API
class ActivityViewSet(viewsets.ModelViewSet):
    """Handles GET, POST, PUT, DELETE for Activities"""
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    
    # Topic 8.3.d: Filtering
    filterset_fields = ['event_date', 'ngo']
    
    # Topic 7.3.a & 7.3.b: Security
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly] 

# Topic 8.1.c, 7.3.c, & 8.3.b: Registration API with Validation
class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    
    # Topic 7.3.a & 7.3.c: Security
    permission_classes = [IsAuthenticated, IsEmployeeOnly] 
    
    def perform_create(self, serializer):
        # 1. Grab the activity the user is trying to register for
        activity = serializer.validated_data['activity']
        
        # 2. TOPIC 8.3.b VALIDATION: Check Slot Availability
        if activity.seats_available() <= 0:
            raise ValidationError({"error": "Registration failed: This event is completely full."})
        
        # 3. TOPIC 8.3.b VALIDATION: Prevent Duplicate API Registrations
        if Registration.objects.filter(employee=self.request.user, activity=activity).exists():
            raise ValidationError({"error": "You are already registered for this event."})

        # 4. If it passes validation, save it!
        serializer.save(employee=self.request.user)