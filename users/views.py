from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from users.forms import UserCreationForm, UserProfileForm


class RegisterView(View):
    """
    View for user registration.
    """

    def get(self, request):
        """
        Handles GET requests by displaying the registration form.
        """
        form = UserCreationForm()
        return render(request, "users/register.html", {"form": form})

    def post(self, request):
        """
        Handles POST requests by validating the form and creating a new user.
        """
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        return render(request, "users/register.html", {"form": form})


class ProfileView(LoginRequiredMixin, View):
    """
    Class-Based View for displaying and updating the user's profile.
    Requires user to be logged in.
    """

    template_name = "users/profile.html"

    def get(self, request, *args, **kwargs):
        """Handles GET requests: displays the profile form."""
        form = UserProfileForm(instance=request.user.profile)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """Handles POST requests: processes form submission."""
        profile_instance = request.user.profile
        form = UserProfileForm(request.POST, request.FILES, instance=profile_instance)

        if form.is_valid():
            # The display_name is saved automatically by form.save()
            form.save(commit=False)

            # Handle the profile picture upload separately
            picture = request.FILES.get("profile_picture_file")
            if picture:
                profile_instance.upload_profile_picture(picture)

            profile_instance.save()
            return redirect("profile")  # Redirect after successful update

        # If form is invalid, re-render the page with errors
        return render(request, self.template_name, {"form": form})
