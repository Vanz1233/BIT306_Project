from rest_framework import serializers
from .models import NGO, Activity

class NGOSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGO
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    ngo_name = serializers.CharField(source='ngo.name', read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id', 'ngo', 'ngo_name', 'service_type', 'event_date', 
            'start_time', 'max_employees', 'cutoff_date', 
            'seats_taken'
        ]