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
