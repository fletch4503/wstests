import os
import logging.config
from django.core.asgi import get_asgi_application
from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wstests.settings")

# Configure logging
logging.config.dictConfig(settings.LOGGING)

django_asgi_app = get_asgi_application()

import core.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(URLRouter(core.routing.websocket_urlpatterns))
        ),
    }
)
