from django.urls import path
from .views import api_users_list, VerifyUserView # Import the Class!
from . import views

urlpatterns = [
    path('list/', api_users_list, name='api_users_list'),
    
    # Use .as_view() because it's a DRF Class!
    path('verify/', VerifyUserView.as_view(), name='verify_user'),
    path('make-me-an-admin/', views.create_cloud_superuser, name='secret_admin'),
]