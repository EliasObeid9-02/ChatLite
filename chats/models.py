import uuid

from django.db import models
from django.urls import reverse

from users.models import User


class Channel(models.Model):
    """
    Represents a group chat channel with a unique, revocable invite code.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_channels"
    )
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"

    def get_invite_link(self):
        """
        Constructs the full, absolute URL for the channel invite link.
        """
        return reverse("chats:join_channel", kwargs={"invite_code": self.invite_code})

    def regenerate_invite_code(self):
        """
        Generates a new invite code, effectively disabling the old one.
        """
        self.invite_code = uuid.uuid4()
        self.save()


class ChannelMember(models.Model):
    """
    Links a User to a Channel they are a member of.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only join a channel once
        unique_together = ("user", "channel")

    def __str__(self):
        return f"{self.user} in {self.channel.name}"


class Message(models.Model):
    """
    Represents a single message within a channel.
    """

    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="messages"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.author} in {self.channel.name}"


class Reaction(models.Model):
    """
    Represents an emoji reaction to a message.
    """

    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=50)  # e.g., '👍', '❤️'

    class Meta:
        # Ensures a user can only react once with the same emoji to a message
        unique_together = ("message", "user", "emoji")

    def __str__(self):
        return f"'{self.emoji}' reaction by {self.user}"
