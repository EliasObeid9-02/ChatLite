from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, TemplateView, View
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from chats.forms import ChannelCreateForm, ChannelUpdateForm, MessageForm
from chats.models import Channel, Message, Reaction


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "chats/home.html"


class ChannelChatView(LoginRequiredMixin, TemplateView):
    template_name = "chats/channel_chat.html"

    def get(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)

        if request.user not in channel.members.all():
            return render(request, "unauthorized.html")

        messages = (
            channel.channel_messages.order_by("timestamp")
            .select_related("sender__profile")
            .prefetch_related("message_reactions__reactor")
        )

        grouped_messages = []
        current_group = None

        for message in messages:
            # Process reactions for each message
            reaction_counts = {}
            user_reacted_emojis = set()
            for reaction in message.message_reactions.all():
                reaction_counts.setdefault(reaction.emoji, 0)
                reaction_counts[reaction.emoji] += 1
                if reaction.reactor == request.user:
                    user_reacted_emojis.add(reaction.emoji)

            message.reaction_counts = reaction_counts
            message.user_reacted_emojis = user_reacted_emojis

            if (
                current_group
                and current_group["sender"] == message.sender
                and (
                    message.timestamp - current_group["last_timestamp"]
                ).total_seconds()
                < 60 * 5  # Group messages within 5 minutes
            ):
                current_group["messages"].append(message)
                current_group["last_timestamp"] = message.timestamp
            else:
                if current_group:
                    grouped_messages.append(current_group)
                current_group = {
                    "sender": message.sender,
                    "avatar": (
                        message.sender.profile.profile_picture
                        if hasattr(message.sender, "profile")
                        and message.sender.profile.profile_picture
                        else "/static/images/default_avatar.png"
                    ),
                    "display_name": (
                        message.sender.profile.display_name
                        if hasattr(message.sender, "profile")
                        else message.sender.username
                    ),
                    "messages": [message],
                    "start_timestamp": message.timestamp,
                    "last_timestamp": message.timestamp,
                }
        if current_group:
            grouped_messages.append(current_group)

        context = {
            "channel": channel,
            "members_count": channel.members.count(),
            "grouped_messages": grouped_messages,
            "form": MessageForm(),
        }
        return render(request, self.template_name, context)


class CreateChannelView(LoginRequiredMixin, CreateView):
    template_name = "chats/channel_create.html"
    form_class = ChannelCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        response = redirect(self.object.get_absolute_url())
        response["HX-Trigger"] = "channelCreated"
        return response


class ChannelView(LoginRequiredMixin, TemplateView):
    template_name = "chats/channel_view.html"
    unauthorized_template_name = "unauthorized.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        channel_id = self.kwargs.get("channel_id")

        channel = get_object_or_404(Channel, id=channel_id)
        context["channel"] = channel
        context["is_owner"] = channel.owner == self.request.user

        if self.request.user == channel.owner:
            context["form"] = ChannelUpdateForm(instance=channel)
        return context

    def post(self, request, *args, **kwargs):
        channel_id = self.kwargs.get("channel_id")
        channel = get_object_or_404(Channel, id=channel_id)

        if request.user != channel.owner:
            return render(request, self.unauthorized_template_name)

        form = ChannelUpdateForm(request.POST, instance=channel)
        if form.is_valid():
            channel.save()
            response = redirect("chats:channel-details", channel_id=channel_id)
            response["HX-Trigger"] = "channelUpdated"
            return response
        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)


class JoinChannelView(LoginRequiredMixin, View):
    invalid_invite_template_name = "chats/invalid_invite.html"

    def get(self, request, invite_code):
        try:
            channel = Channel.objects.get(invite_code=invite_code)
        except Channel.DoesNotExist:
            return render(request, self.invalid_invite_template_name, status=404)

        user = request.user
        # if the user is not a member we add them and redirect to the chat
        if user not in channel.members.all():
            channel.members.add(user)
        return redirect(channel.get_absolute_url())


class GenerateInviteCodeView(LoginRequiredMixin, View):
    invite_link_template_name = "chats/partials/_invite_link.html"
    unauthorized_template_name = "unauthorized.html"

    def post(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)

        if request.user != channel.owner:
            return render(request, self.unauthorized_template_name)

        channel.generate_invite_code()
        context = {"channel": channel}
        return render(request, self.invite_link_template_name, context)


class ToggleReactionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        message_id = request.POST.get("message_id")
        emoji = request.POST.get("emoji")

        message = get_object_or_404(Message, id=message_id)
        reactor = request.user

        try:
            reaction = Reaction.objects.get(
                message=message, reactor=reactor, emoji=emoji
            )
            reaction.delete()
        except Reaction.DoesNotExist:
            Reaction.objects.create(message=message, reactor=reactor, emoji=emoji)

        # Re-fetch reactions for the message to update the count
        reactions = message.message_reactions.select_related("reactor")
        reaction_counts = {}
        user_reacted_emojis = set()

        for reaction in reactions:
            reaction_counts.setdefault(reaction.emoji, 0)
            reaction_counts[reaction.emoji] += 1
            if reaction.reactor == request.user:
                user_reacted_emojis.add(reaction.emoji)

        context = {
            "message_id": message_id,
            "reaction_counts": reaction_counts,
            "user_reacted_emojis": user_reacted_emojis,
            "current_user_id": str(request.user.id),
        }
        return render(request, "chats/partials/_reactions_list.html", context)
