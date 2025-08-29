from django.urls import path

from chats.views import (
    ChannelChatView,
    ChannelView,
    CreateChannelView,
    GenerateInviteCodeView,
    HomeView,
    JoinChannelView,
)

app_name = "chats"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("channel/create/", CreateChannelView.as_view(), name="channel-create"),
    path("channel/<uuid:channel_id>/", ChannelChatView.as_view(), name="channel-chat"),
    path(
        "channel/<uuid:channel_id>/details/",
        ChannelView.as_view(),
        name="channel-details",
    ),
    path(
        "channel/join/<uuid:invite_code>/",
        JoinChannelView.as_view(),
        name="channel-join",
    ),
    path(
        "channel/<uuid:channel_id>/generate-invite/",
        GenerateInviteCodeView.as_view(),
        name="generate-invite",
    ),
]
