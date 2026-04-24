from django.urls import path
from .views import RegistrationCreateView, RegistrationListView, RegistrationStatsView

urlpatterns = [
    # The endpoint for clicking Register/Withdraw
    path('toggle/', RegistrationCreateView.as_view(), name='toggle_registration'),
    
    # The endpoint to see all records
    path('list/', RegistrationListView.as_view(), name='list_registrations'),
    
    # The endpoint to power the Admin Chart
    path('stats/', RegistrationStatsView.as_view(), name='registration_stats'),
]