from django.urls import path

from chats.views import (
    ChannelView,
    CreateChannelView,
    HomeView,
    JoinChannelView,
    RegenerateInviteCodeView,
)

app_name = "chats"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("channel/create/", CreateChannelView.as_view(), name="create-channel"),
    path("channel/<uuid:channel_id>/", ChannelView.as_view(), name="channel-view"),
    path("join/<uuid:invite_code>/", JoinChannelView.as_view(), name="join-channel"),
    path(
        "channel/<uuid:channel_id>/regenerate-invite/",
        RegenerateInviteCodeView.as_view(),
        name="regenerate-invite-code",
    ),
]
