"""
ASGI config for project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
from django.core.asgi import get_asgi_application

# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# TEMPORARIAMENTE COMENTADO - Configurar depois
# from apps.game import routing as game_routing

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             game_routing.websocket_urlpatterns
#         )
#     ),
# })

# Por enquanto, apenas HTTP
application = django_asgi_app
