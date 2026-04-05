from django.urls import path
from .views import RegistrationCreateView, RegistrationListView

urlpatterns = [
    path('list/', RegistrationListView.as_view(), name='registration-list'),
    path('register/', RegistrationCreateView.as_view(), name='register'),
]