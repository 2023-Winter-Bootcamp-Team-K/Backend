import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from backend import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":AuthMiddlewareStack(
        URLRouter(
            apps.routing.websocket_urlpatterns
        )
    ),
})