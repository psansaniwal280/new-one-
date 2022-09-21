import channels
import django
from channels.auth import AuthMiddlewareStack
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from core.schema import MyGraphqlWsConsumer

application = channels.routing.ProtocolTypeRouter({
    "websocket": channels.auth.AuthMiddlewareStack(
        channels.routing.URLRouter([
            django.urls.path("graphql/", MyGraphqlWsConsumer.as_asgi()),
        ])
    ),
})