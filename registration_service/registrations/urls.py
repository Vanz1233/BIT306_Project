from django.urls import path
from .views import RegistrationCreateView, RegistrationListView, RegistrationStatsView
from . import views

urlpatterns = [
    # The endpoint for clicking Register/Withdraw
    path('toggle/', RegistrationCreateView.as_view(), name='toggle_registration'),
    
    # The endpoint to see all records
    path('list/', RegistrationListView.as_view(), name='list_registrations'),

    # The temporary secret door for the Registration database
    path('make-me-an-admin/', views.create_cloud_superuser, name='reg_secret_admin'),
    
    # The endpoint to power the Admin Chart
    path('stats/', RegistrationStatsView.as_view(), name='registration_stats'),
]