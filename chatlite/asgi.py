import os

from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early to ensure settings are configured.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatlite.settings")
django_asgi_app = get_asgi_application()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack

from chats.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": SessionMiddlewareStack(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns),
            )
        ),
    }
)
