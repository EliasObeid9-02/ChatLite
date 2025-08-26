from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, RedirectView, TemplateView

from chats.models import Channel, ChannelMember
from core.mixins import HtmxMixin


class ChannelContextMixin:
    """A mixin that adds the list of user's channels to the context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["user_channels"] = ChannelMember.objects.filter(
                user=self.request.user
            ).select_related("channel")
        return context


class HomeView(HtmxMixin, ChannelContextMixin, TemplateView):
    """
    Acts as a router based on authentication status.
    - Authenticated users see the main application.
    - Unauthenticated users are redirected to the login page.
    """

    template_name = "chats/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        return super().dispatch(request, *args, **kwargs)


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
