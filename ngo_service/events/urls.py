from django.urls import path
from .views import NGOListView, ActivityListView, ActivityDetailView
from . import views

urlpatterns = [
    path('list/', NGOListView.as_view(), name='ngo-list'),
    path('activities/', ActivityListView.as_view(), name='activity-list'),
    path('activities/<int:pk>/', ActivityDetailView.as_view(), name='activity-detail'),
    path('make-me-an-admin/', views.create_cloud_superuser, name='ngo_secret_admin'),
    path('api/events/update-seats/', views.update_seat_count, name='update_seat_count'),
]