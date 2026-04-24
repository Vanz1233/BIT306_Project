from rest_framework import serializers
from .models import NGO, Activity, Registration

class NGOSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGO
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    ngo_name = serializers.CharField(source='ngo.name', read_only=True)
    seats_taken = serializers.IntegerField(read_only=True)
    seats_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'ngo', 'ngo_name', 'service_type', 'event_date', 
            'start_time', 'max_employees', 'cutoff_date', 
            'seats_taken', 'seats_available'
        ]

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = '__all__'
        read_only_fields = ['employee']