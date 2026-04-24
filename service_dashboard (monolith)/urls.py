from django.urls import path
from . import views

urlpatterns = [
    # Landing Page
    path('', views.dashboard, name='dashboard'),

    path('admin-dashboard/scanner/', views.scanner_prototype, name='scanner_prototype'),
    
    # Kept as event_id because your view_ticket function still uses 'event_id'
    path('ticket/<int:event_id>/', views.view_ticket, name='view_ticket'),

    # UPDATED: Changed <int:ngo_id> to <int:activity_id>
    path('register/<int:activity_id>/', views.register_event, name='register'),

    # UPDATED: Changed <int:ngo_id> to <int:activity_id>
    path('cancel/<int:activity_id>/', views.cancel_registration, name='cancel'),

    path('smart-redirect/', views.smart_redirect, name='smart_redirect'),
]

