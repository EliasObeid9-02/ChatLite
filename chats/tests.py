import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from chats.models import Channel, Message, Reaction

UserModel = get_user_model()


class ChatModelsTest(TestCase):
    def setUp(self):
        self.user1 = UserModel.objects.create_user(
            username="testuser1", email="test1@example.com", password="password123"
        )
        self.user2 = UserModel.objects.create_user(
            username="testuser2", email="test2@example.com", password="password123"
        )
        self.channel = Channel.objects.create(
            name="Test Channel", owner=self.user1, description="A channel for testing"
        )

    def test_channel_creation(self):
        self.assertEqual(Channel.objects.count(), 1)
        self.assertEqual(self.channel.name, "Test Channel")
        self.assertEqual(self.channel.owner, self.user1)
        self.assertTrue(isinstance(self.channel.id, uuid.UUID))
        self.assertTrue(isinstance(self.channel.invite_code, uuid.UUID))
        self.assertIn(
            self.user1, self.channel.members.all()
        )  # Owner should be a member

    def test_channel_get_invite_link(self):
        expected_url = reverse_lazy(
            "chats:channel-join", kwargs={"invite_code": self.channel.invite_code}
        )
        self.assertEqual(self.channel.get_invite_link(), expected_url)

    def test_channel_generate_invite_code(self):
        old_invite_code = self.channel.invite_code
        self.channel.generate_invite_code()
        self.assertNotEqual(self.channel.invite_code, old_invite_code)
        self.channel.refresh_from_db()  # Ensure the change is saved and reloaded
        self.assertNotEqual(self.channel.invite_code, old_invite_code)

    def test_channel_get_absolute_url(self):
        expected_url = reverse_lazy(
            "chats:channel-chat", kwargs={"channel_id": self.channel.id}
        )
        self.assertEqual(self.channel.get_absolute_url(), expected_url)

    def test_channel_str_representation(self):
        self.assertEqual(
            str(self.channel), f"Channel: 'Test Channel' owned by User: '{self.user1}'"
        )

    def test_message_creation(self):
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Hello everyone!"
        )
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(message.channel, self.channel)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello everyone!")
        self.assertIsNotNone(message.timestamp)

    def test_message_str_representation(self):
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Hello everyone!"
        )
        self.assertEqual(
            str(message),
            f"Message: 'Hello everyone!' sent by User: '{self.user1}' in Channel: '{self.channel}'",
        )

    def test_reaction_creation(self):
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Hello everyone!"
        )
        reaction = Reaction.objects.create(
            message=message, reactor=self.user2, emoji="👍"
        )
        self.assertEqual(Reaction.objects.count(), 1)
        self.assertEqual(reaction.message, message)
        self.assertEqual(reaction.reactor, self.user2)
        self.assertEqual(reaction.emoji, "👍")

    def test_reaction_unique_together(self):
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Hello everyone!"
        )
        Reaction.objects.create(message=message, reactor=self.user2, emoji="👍")
        with self.assertRaises(Exception):  # IntegrityError or similar
            Reaction.objects.create(message=message, reactor=self.user2, emoji="👍")

    def test_reaction_str_representation(self):
        message = Message.objects.create(
            channel=self.channel, sender=self.user1, content="Hello everyone!"
        )
        reaction = Reaction.objects.create(
            message=message, reactor=self.user2, emoji="👍"
        )
        self.assertEqual(
            str(reaction),
            f"Reaction: '👍' by User '{self.user2}' on Message: '{message}'",
        )
