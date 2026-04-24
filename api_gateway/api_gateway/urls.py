from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Change 'api/' to '' so it listens to the root URL
    path('', include('gateway.urls')), 
]
