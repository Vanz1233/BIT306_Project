from rest_framework import generics
from .models import NGO, Activity
from .serializers import NGOSerializer, ActivitySerializer

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
