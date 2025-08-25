from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from chats.models import Channel, ChannelMember


class CreateChannelView(LoginRequiredMixin, View):
    """View to handle channel creation."""

    def get(self, request, *args, **kwargs):
        return render(request, "chats/create_channel.html")

    def post(self, request, *args, **kwargs):
        channel_name = request.POST.get("name")
        channel_description = request.POST.get("description")

        # Create the channel
        channel = Channel.objects.create(
            name=channel_name, description=channel_description, creator=request.user
        )

        # Automatically add the creator as a member
        ChannelMember.objects.create(user=request.user, channel=channel)
        return redirect("channel_view", channel_id=channel.id)


class JoinChannelView(LoginRequiredMixin, View):
    """View to handle a user joining a channel via invite link."""

    def get(self, request, invite_code, *args, **kwargs):
        # Find the channel using the invite_code
        # Because every invite code is unique to a single channel
        # when an invite code is overridden it will not work anymore
        channel = get_object_or_404(Channel, invite_code=invite_code)
        ChannelMember.objects.get_or_create(user=request.user, channel=channel)
        return redirect("channel_view", channel_id=channel.id)


class RegenerateInviteCodeView(LoginRequiredMixin, View):
    """Allows the channel creator to regenerate the invite code."""

    def post(self, request, channel_id, *args, **kwargs):
        channel = get_object_or_404(Channel, id=channel_id)

        # Security check: Only the channel creator can regenerate the link
        if channel.creator != request.user:
            return HttpResponseForbidden(
                "You are not authorized to perform this action."
            )

        channel.regenerate_invite_code()
        return redirect("channel_view", channel_id=channel.id)


class ChannelView(LoginRequiredMixin, View):
    """View to display a channel's chat interface."""

    def get(self, request, channel_id, *args, **kwargs):
        channel = get_object_or_404(Channel, id=channel_id)
        messages = channel.messages.order_by("timestamp").all()
        return render(
            request, "chats/channel.html", {"channel": channel, "messages": messages}
        )
