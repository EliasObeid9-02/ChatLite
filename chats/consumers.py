import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from chats.models import Channel, Message, Reaction

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
                profile_picture = user.profile.profile_picture
        return {"display_name": display_name, "profile_picture": profile_picture}

    async def _save_message(self, channel_id, sender, content):
        channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        message = await sync_to_async(Message.objects.create)(
            channel=channel, sender=sender, content=content
        )
        return message

    async def _get_message_with_reactions(self, message_id, current_user_id):
        message = await sync_to_async(Message.objects.get)(id=message_id)
        reactions = await sync_to_async(list)(
            message.message_reactions.select_related("reactor")
        )

        reaction_counts = {}
        user_reacted_emojis = set()

        for reaction in reactions:
            reaction_counts.setdefault(reaction.emoji, 0)
            reaction_counts[reaction.emoji] += 1
            if reaction.reactor.id == current_user_id:
                user_reacted_emojis.add(reaction.emoji)

        return message, reaction_counts, user_reacted_emojis

    async def _save_message(self, channel_id, sender, content):
        channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        message = await sync_to_async(Message.objects.create)(
            channel=channel, sender=sender, content=content
        )
        return message

    async def _toggle_reaction(self, message_id, reactor, emoji):
        message = await sync_to_async(Message.objects.get)(id=message_id)
        try:
            reaction = await sync_to_async(Reaction.objects.get)(
                message=message, reactor=reactor, emoji=emoji
            )
            await sync_to_async(reaction.delete)()
            return False  # Reaction removed
        except Reaction.DoesNotExist:
            await sync_to_async(Reaction.objects.create)(
                message=message, reactor=reactor, emoji=emoji
            )
            return True  # Reaction added

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type")

        if message_type == "message":
            message_content = text_data_json["message"]
            sender = self.scope["user"]

            # Save message to database
            message = await self._save_message(self.channel_id, sender, message_content)

            user_profile_data = await sync_to_async(self._get_user_profile_data)(sender)

            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    "type": "chat_message",
                    "message_id": str(message.id),
                    "message_content": message.content,
                    "sender_id": str(sender.id),
                    "sender_username": sender.username,
                    "sender_display_name": user_profile_data["display_name"],
                    "sender_avatar": user_profile_data["profile_picture"],
                    "timestamp": message.timestamp.isoformat(),
                },
            )
        elif message_type == "reaction":
            message_id = text_data_json["message_id"]
            emoji = text_data_json["emoji"]
            reactor = self.scope["user"]

            await self._toggle_reaction(message_id, reactor, emoji)

            # Fetch updated reactions and send update to group
            _, reaction_counts, user_reacted_emojis = (
                await self._get_message_with_reactions(message_id, reactor.id)
            )

            await self.channel_layer.group_send(
                self.channel_group_name,
                {
                    "type": "reaction_update",
                    "message_id": str(message_id),
                    "reaction_counts": reaction_counts,
                },
            )

    # Receive message from channel group
    async def chat_message(self, event):
        message_id = event["message_id"]
        message_content = event["message_content"]
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
                "message_id": message_id,
                "message_content": message_content,
                "sender_id": sender_id,
                "sender_username": sender_username,
                "sender_display_name": sender_display_name,
                "sender_avatar": sender_avatar,
                "timestamp": timestamp,
                "reaction_counts": {},  # New messages have no reactions initially
                "user_reacted_emojis": [],
            },
        )

        # Send HTML to WebSocket
        await self.send(text_data=json.dumps({"html": html, "message_data": event}))

    async def reaction_update(self, event):
        message_id = event["message_id"]
        reaction_counts = event["reaction_counts"]
        current_user_id = self.scope["user"].id

        # Re-fetch reactions for the current user
        message = await sync_to_async(Message.objects.get)(id=message_id)
        user_reactions = await sync_to_async(list)(
            message.message_reactions.filter(reactor=current_user_id).values_list(
                "emoji", flat=True
            )
        )
        user_reacted_emojis = set(user_reactions)

        # Render the reactions using a partial template
        html = render_to_string(
            "chats/partials/_reactions_list.html",
            {
                "message_id": message_id,
                "reaction_counts": reaction_counts,
                "user_reacted_emojis": user_reacted_emojis,
                "current_user_id": str(current_user_id),
            },
        )

        # Send HTML to WebSocket
        await self.send(
            text_data=json.dumps(
                {"type": "reaction_update", "message_id": message_id, "html": html}
            )
        )
