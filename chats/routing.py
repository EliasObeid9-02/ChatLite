from django.urls import re_path

from chats import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<channel_id>[0-9a-fA-F-]+)/$", consumers.ChatConsumer.as_asgi()
    ),
]
