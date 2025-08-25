from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from users.models import User, UserProfile


class UserCreationForm(BaseUserCreationForm):
    """
    A form for creating new users. Includes all the required
    fields, plus a repeated password.
    """

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class UserProfileForm(forms.ModelForm):
    """
    Form for updating the UserProfile.
    """

    class Meta:
        model = UserProfile
        fields = ("display_name", "profile_picture_file")

    profile_picture_file = forms.ImageField(
        required=False, label="Upload New Profile Picture"
    )
