from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, View

from chats.forms import ChannelCreateForm, ChannelUpdateForm
from chats.models import Channel


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "chats/home.html"


# TODO: implement
class ChannelChatView(LoginRequiredMixin, View):
    template_name = "chats/channel_chat.html"

    def get(self, request, channel_id):
        return HttpResponse(f"Channel View for ID: {channel_id}")


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
            return render(request, "unauthorized.html")

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
    def get(self, request, invite_code):
        try:
            channel = Channel.objects.get(invite_code=invite_code)
        except Channel.DoesNotExist:
            return render(request, "chats/invalid_invite.html", status=404)

        user = request.user
        # if the user is not a member we add them and redirect to the chat
        if user not in channel.members.all():
            channel.members.add(user)
        return redirect(channel.get_absolute_url())


class GenerateInviteCodeView(LoginRequiredMixin, View):
    def post(self, request, channel_id):
        channel = get_object_or_404(Channel, id=channel_id)

        if request.user != channel.owner:
            return render(request, "unauthorized.html")

        channel.generate_invite_code()
        context = {"channel": channel}
        return render(request, "chats/partials/_invite_link.html", context)
