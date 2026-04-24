from django.urls import path
from .views import gateway_toggle_registration, route_request, frontend_dashboard, frontend_login, frontend_logout

urlpatterns = [
    # 1. Frontend HTML Routes
    path('', frontend_dashboard, name='dashboard'),
    path('login/', frontend_login, name='gateway_login'),
    path('logout/', frontend_logout, name='gateway_logout'),

    path('toggle-registration/' , gateway_toggle_registration, name='gateway_toggle'),
    
    # 2. The API Traffic Cop
    path('api/<path:path>', route_request, name='api_gateway'),
]