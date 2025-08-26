from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from users.models import User, UserProfile


class UserRegisterForm(BaseUserCreationForm):
    """
    A registration form that includes a display_name field.
    """

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    widgets = {
        "username": forms.TextInput(attrs={"class": "form-control"}),
        "email": forms.EmailInput(attrs={"class": "form-control"}),
        "password1": forms.PasswordInput(attrs={"class": "form-control"}),
        "password2": forms.PasswordInput(attrs={"class": "form-control"}),
    }

    def save(self, commit=True):
        """
        Save the user and then save the display_name to the user's profile.
        """
        user = super().save(commit=commit)
        return user


class AuthenticationForm(BaseAuthenticationForm):
    """
    Login form to allow login with either username or email.
    """

    widgets = {
        "identifier": forms.TextInput(attrs={"class": "form-control"}),
        "password": forms.PasswordInput(attrs={"class": "form-control"}),
    }

    def clean(self):
        identifier = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if identifier and password:
            # Try to find a user by username or email
            user_by_username = User.objects.filter(username=identifier).first()
            user_by_email = User.objects.filter(email=identifier).first()

            if user_by_username:
                self.user_cache = authenticate(
                    self.request, username=user_by_username.username, password=password
                )
            elif user_by_email:
                self.user_cache = authenticate(
                    self.request, username=user_by_email.username, password=password
                )
            else:
                # If no user found by either, fail authentication
                self.user_cache = None

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """
    Form for updating the UserProfile.
    """

    profile_picture_file = forms.ImageField(
        required=False,
        label="Upload New Profile Picture",
    )

    widgets = {
        "display_name": forms.TextInput(attrs={"class": "form-control"}),
        "profile_picture_file": forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/png, image/jpeg, image/gif",
            }
        ),
    }

    class Meta:
        model = UserProfile
        fields = ("display_name",)
