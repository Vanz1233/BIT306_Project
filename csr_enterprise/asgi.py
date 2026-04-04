import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import service_dashboard.routing 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'csr_enterprise.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        service_dashboard.routing.websocket_urlpatterns
    ),
})
