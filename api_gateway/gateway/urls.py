from django.urls import path
from .views import gateway_toggle_registration, route_request, frontend_dashboard, frontend_login, frontend_logout
from . import views

urlpatterns = [
    # 1. Frontend HTML Routes
    path('', frontend_dashboard, name='dashboard'),
    path('login/', frontend_login, name='gateway_login'),
    path('logout/', frontend_logout, name='gateway_logout'),

    path('toggle-registration/' , gateway_toggle_registration, name='gateway_toggle'),
    path('notifications/', views.user_notifications, name='user_notifications'),
    # 2. The API Traffic Cop
    path('api/<path:path>', route_request, name='api_gateway'),
]