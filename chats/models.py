import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse_lazy

UserModel = get_user_model()


class Channel(models.Model):
    """
    Represents a group chat with a unique, revocable invite code.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        to=UserModel, on_delete=models.CASCADE, related_name="created_channels"
    )
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=True)
    members = models.ManyToManyField(to=UserModel, related_name="member_of")

    def save(self, *args, **kwargs):
        """
        Overrides the save method to add the owner as a member upon creation.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.members.add(self.owner)

    def get_invite_link(self):
        """Constructs the full URL of for joining a channel."""
        return reverse_lazy(
            "chats:join-channel", kwargs={"invite_code": self.invite_code}
        )

    def generate_invite_code(self):
        """Creates a new invite link invalidating the old one."""
        self.invite_code = uuid.uuid4()
        self.save()

    def __str__(self):
        return f"Channel: '{self.name}' owned by User: '{self.owner}'"


class Message(models.Model):
    """
    Represents a message in a channel
    """

    channel = models.ForeignKey(
        to=Channel, on_delete=models.CASCADE, related_name="channel_messages"
    )
    sender = models.ForeignKey(
        to=UserModel, on_delete=models.SET_NULL, related_name="user_messages", null=True
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message: '{self.content}' sent by User: '{self.sender}' in Channel: '{self.channel}'"


class Reaction(models.Model):
    """
    Represents an emoji reaction on a message.
    """

    class Meta:
        unique_together = ("message", "reactor", "emoji")

    message = models.ForeignKey(
        to=Message, on_delete=models.CASCADE, related_name="message_reactions"
    )
    reactor = models.ForeignKey(
        to=UserModel, on_delete=models.CASCADE, related_name="user_reactions"
    )
    emoji = models.CharField(max_length=50)

    def __str__(self):
        return f"Reaction: '{self.emoji}' by User '{self.reactor}' on Message: '{self.message}'"

