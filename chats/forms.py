from django import forms

from chats.models import Channel, Message


class ChannelCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.owner = self.user
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Channel
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Channel Name",
                    "class": "input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Channel Description (optional)",
                    "rows": 3,
                    "class": "textarea",
                }
            ),
        }


class ChannelUpdateForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "New Channel Name",
                    "class": "input",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "New Channel Description (optional)",
                    "rows": 3,
                    "class": "textarea",
                }
            ),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("content",)
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "placeholder": "Type your message...",
                    "class": "input",
                }
            ),
        }
