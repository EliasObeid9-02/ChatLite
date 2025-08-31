import json
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from chats.models import Channel, Message, Reaction

UserModel = get_user_model()
logger = logging.getLogger(__name__)


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

    @sync_to_async
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

    async def _get_last_two_messages(self, channel_id):
        try:
            messages = await sync_to_async(list)(
                Message.objects.select_related("sender")
                .filter(channel_id=channel_id)
                .order_by("-timestamp")[:2]
            )
            return messages
        except Message.DoesNotExist:
            return None

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
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")

            if "content" in text_data_json:
                message_type = "message"
            elif "emoji" in text_data_json:
                message_type = "reaction"

            if message_type == "message":
                message_content = text_data_json["content"]
                sender = self.scope["user"]

                # Save message to database
                message = await self._save_message(
                    self.channel_id, sender, message_content
                )

                user_profile_data = await self._get_user_profile_data(sender)

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
        except Exception:
            logger.exception("Error in receive")

    # Receive message from channel group
    async def chat_message(self, event):
        try:
            # Activate timezone from user's cookie
            tzname = self.scope["cookies"].get("django_timezone")
            if tzname:
                try:
                    timezone.activate(ZoneInfo(tzname))
                except ZoneInfoNotFoundError:
                    timezone.deactivate()
            else:
                timezone.deactivate()

            message_id = event["message_id"]
            message_content = event["message_content"]
            sender_id = event["sender_id"]
            sender_display_name = event["sender_display_name"]
            sender_avatar = event["sender_avatar"]
            timestamp_str = event["timestamp"]
            timestamp = datetime.fromisoformat(timestamp_str)

            messages = await self._get_last_two_messages(self.channel_id)
            should_group = False

            if len(messages) == 2:
                new_message = messages[0]
                previous_message = messages[1]

                if str(new_message.id) == message_id:
                    time_diff = new_message.timestamp - previous_message.timestamp
                    if (
                        previous_message.sender.id == uuid.UUID(sender_id)
                        and time_diff.total_seconds() < 60 * 5
                    ):
                        should_group = True

            html = ""
            if should_group:
                # Render only the single message and append it to the last group
                single_message_html = await sync_to_async(render_to_string)(
                    "chats/partials/_single_message.html",
                    {
                        "message_id": message_id,
                        "message_content": message_content,
                        "sender_id": sender_id,
                        "timestamp": timestamp,
                        "reaction_counts": {},
                        "user_reacted_emojis": [],
                    },
                )
                html = f'<div hx-swap-oob="beforeend:.message-group:last-child .messages">{single_message_html}</div>'
            else:
                # Render a new message group and append it to the chat log
                group = {
                    "avatar": sender_avatar,
                    "display_name": sender_display_name,
                    "start_timestamp": timestamp,
                    "messages": [
                        {
                            "id": message_id,
                            "content": message_content,
                            "sender": {"id": sender_id},
                            "timestamp": timestamp,
                            "reaction_counts": {},
                            "user_reacted_emojis": [],
                        }
                    ],
                }
                message_group_html = await sync_to_async(render_to_string)(
                    "chats/partials/_message_group.html", {"group": group}
                )
                html = (
                    f'<div hx-swap-oob="beforeend:#chat-log">{message_group_html}</div>'
                )

                # If it's the first message, also remove the placeholder
                channel = await sync_to_async(Channel.objects.get)(id=self.channel_id)
                message_count = await sync_to_async(channel.channel_messages.count)()
                if message_count == 1:
                    html += '<p id="no-messages-p" hx-swap-oob="delete"></p>'

            await self.send(text_data=html)
        except Exception:
            logger.exception("Error in chat_message")

    async def reaction_update(self, event):
        try:
            message_id = event["message_id"]
            reaction_counts = event["reaction_counts"]
            current_user_id = self.scope["user"].id

            # Re-fetch reactions for the current user
            message = await sync_to_async(Message.objects.get)(id=message_id)
            user_reactions = await sync_to_async(list)(
                message.message_reactions.filter(
                    reactor=current_user_id
                ).values_list("emoji", flat=True)
            )
            user_reacted_emojis = set(user_reactions)

            # Render the reactions using a partial template
            html = await sync_to_async(render_to_string)(
                "chats/partials/_reactions_list.html",
                {
                    "message_id": message_id,
                    "reaction_counts": reaction_counts,
                    "user_reacted_emojis": user_reacted_emojis,
                    "current_user_id": str(current_user_id),
                },
            )

            # Send HTML to WebSocket with OOB swap
            html = f'<div id="reactions-for-message-{message_id}" hx-swap-oob="outerHTML">{html}</div>'
            await self.send(text_data=html)
        except Exception:
            logger.exception("Error in reaction_update")
