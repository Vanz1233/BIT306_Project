from django.urls import path
from .views import api_users_list, VerifyUserView # Import the Class!

urlpatterns = [
    path('list/', api_users_list, name='api_users_list'),
    
    # Use .as_view() because it's a DRF Class!
    path('verify/', VerifyUserView.as_view(), name='verify_user'),
]