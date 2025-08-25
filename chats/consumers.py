import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from chats.models import Channel, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles new WebSocket connections."""
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        self.channel_group_name = f"chat_{self.channel_id}"
        self.user = self.scope["user"]

        # Only allow authenticated users to connect
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join channel group
        await self.channel_layer.group_add(self.channel_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        """Handles WebSocket disconnections."""
        # Leave channel group
        await self.channel_layer.group_discard(
            self.channel_group_name, self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receives a message from the WebSocket, saves it to the database,
        and broadcasts it to the channel group.
        """
        data = json.loads(text_data)
        message_content = data.get("message")

        if not message_content:
            return

        # Save the message to the database
        message = await self.create_new_message(message_content)

        # Render the message to an HTML fragment
        message_html = render_to_string("chats/_message.html", {"message": message})

        # Broadcast the HTML to the channel group
        await self.channel_layer.group_send(
            self.channel_group_name,
            {"type": "chat_message", "message_html": message_html},
        )

    async def chat_message(self, event):
        """
        Receives a message from the channel group and sends the
        pre-rendered HTML to the WebSocket.
        """
        message_html = event["message_html"]
        # Send the HTML fragment to the client
        await self.send(text_data=message_html)

    @database_sync_to_async
    def create_new_message(self, content):
        """
        Saves a new message to the database. This runs in a synchronous
        thread to safely interact with the Django ORM.
        """
        channel = Channel.objects.get(id=self.channel_id)
        return Message.objects.create(
            channel=channel, author=self.user, content=content
        )
