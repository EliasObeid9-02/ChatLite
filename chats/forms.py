from django import forms

from chats.models import Channel


class ChannelCreationForm(forms.ModelForm):
    """
    A form for creating a new Channel.
    """

    class Meta:
        model = Channel
        fields = ("name", "description")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter a channel name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter an optional description for the channel",
                    "rows": 4,
                }
            ),
        }
