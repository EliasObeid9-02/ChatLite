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
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Username",
                    "class": "input",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Email",
                    "class": "input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "input",
            }
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={
                "placeholder": "Password Confirmation",
                "class": "input",
            }
        )


class AuthenticationForm(BaseAuthenticationForm):
    """
    Login form to allow login with either username or email.
    """

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or Email"
        self.fields["username"].widget = forms.TextInput(
            attrs={
                "placeholder": "Username or Email",
                "class": "input",
            }
        )
        self.fields["password"].widget = forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "input",
            }
        )


class UserProfileForm(forms.ModelForm):
    """
    Form for updating the UserProfile.
    """

    class Meta:
        model = UserProfile
        fields = ("display_name",)
        widgets = {
            "display_name": forms.TextInput(
                attrs={
                    "placeholder": "Display name",
                    "class": "input",
                }
            ),
        }
