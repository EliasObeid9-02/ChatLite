import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from chats.models import Message, Channel

UserModel = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        self.channel_group_name = f"chat_{self.channel_id}"

        # Join channel group
        await self.channel_layer.group_add(self.channel_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave channel group
        await self.channel_layer.group_discard(
            self.channel_group_name, self.channel_name
        )

    def _get_user_profile_data(self, user):
        display_name = user.username
        profile_picture = "/static/images/default_avatar.png"

        if hasattr(user, "profile"):
            display_name = user.profile.display_name
            if user.profile.profile_picture:
                profile_picture = user.profile.profile_picture.url
        return {"display_name": display_name, "profile_picture": profile_picture}

    async def _save_message(self, channel_id, sender, content):
        channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        message = await sync_to_async(Message.objects.create)(
            channel=channel, sender=sender, content=content
        )
        return message

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json["message"]
        sender = self.scope["user"]

        # Save message to database
        message = await self._save_message(self.channel_id, sender, message_content)

        user_profile_data = await sync_to_async(self._get_user_profile_data)(sender)

        await self.channel_layer.group_send(
            self.channel_group_name,
            {
                "type": "chat_message",
                "message": message.content,
                "sender_id": str(sender.id),
                "sender_username": sender.username,
                "sender_display_name": user_profile_data["display_name"],
                "sender_avatar": user_profile_data["profile_picture"],
                "timestamp": message.timestamp.isoformat(),
            },
        )

    # Receive message from channel group
    async def chat_message(self, event):
        message = event["message"]
        sender_id = event["sender_id"]
        sender_username = event["sender_username"]
        sender_display_name = event["sender_display_name"]
        sender_avatar = event["sender_avatar"]
        timestamp = event["timestamp"]

        # Render the message using a partial template
        # This will be sent to the frontend to be appended/grouped
        html = render_to_string(
            "chats/partials/_single_message.html",
            {
                "message_content": message,
                "sender_id": sender_id,
                "sender_username": sender_username,
                "sender_display_name": sender_display_name,
                "sender_avatar": sender_avatar,
                "timestamp": timestamp,
            },
        )

        # Send HTML to WebSocket
        await self.send(text_data=json.dumps({"html": html, "message_data": event}))
