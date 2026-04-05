from django.urls import path
from .views import route_request

urlpatterns = [
    # Captures ANY path after /api/ and sends it to the router
    path('<path:path>', route_request, name='api_gateway'),
]