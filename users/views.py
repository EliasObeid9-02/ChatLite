from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from core.mixins import HtmxMixin, RedirectIfAuthenticatedMixin
from users.forms import AuthenticationForm, UserProfileForm, UserRegisterForm

UserModel = get_user_model()


class HomeView(HtmxMixin, TemplateView):
    """
    Acts as a router based on authentication status.
    - Authenticated users see the main application.
    - Unauthenticated users are redirected to the login page.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        # If authenticated, render the main app template
        self.template_name = "chats/home.html"
        return super().dispatch(request, *args, **kwargs)


class LoginView(RedirectIfAuthenticatedMixin, HtmxMixin, auth_views.LoginView):
    """
    Custom login view that handles HTMX redirects.
    """

    form_class = AuthenticationForm
    template_name = "users/login.html"

    def form_valid(self, form):
        """
        Called on a successful form submission.
        """
        login(self.request, form.get_user())

        if self.is_htmx_request():
            response = HttpResponse()
            response["HX-Redirect"] = self.get_success_url()
            return response
        else:
            return super().form_valid(form)


class LogoutView(HtmxMixin, TemplateView):
    """
    Logs the user out and forces a full-page redirect for HTMX requests.
    """

    def post(self, request, *args, **kwargs):
        logout(request)
        redirect_url = reverse_lazy("users:login")

        if self.is_htmx_request():
            response = HttpResponse()
            response["HX-Redirect"] = redirect_url
            return response
        return redirect(redirect_url)


class RegisterView(RedirectIfAuthenticatedMixin, HtmxMixin, CreateView):
    """
    View for user registration using the custom form with a display_name field.
    """

    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class ProfileView(HtmxMixin, LoginRequiredMixin, TemplateView):
    """
    Displays a user's profile.
    - If the visitor is the profile owner, it also displays and
      processes a form to update the profile.
    - Otherwise, it's a read-only view.
    """

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        """
        Fetches the profile and determines if the current user is the owner.
        """
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("user_id")

        # Fetch the user profile based on the user_id from the URL
        profile_user = get_object_or_404(UserModel, id=user_id)
        context["profile"] = profile_user.profile

        # Check if the logged-in user is the owner of the profile
        is_owner = self.request.user == profile_user
        context["is_owner"] = is_owner

        if is_owner:
            # If the user is the owner, add the update form to the context
            context["form"] = UserProfileForm(instance=profile_user.profile)

        return context

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        profile_user = get_object_or_404(UserModel, id=user_id)

        if request.user != profile_user:
            return HttpResponseForbidden("You are not authorized to edit this profile.")

        form = UserProfileForm(
            request.POST, request.FILES, instance=profile_user.profile
        )
        if form.is_valid():
            profile_instance = form.save(commit=False)
            picture = request.FILES.get("profile_picture_file")

            if picture:
                profile_instance.upload_profile_picture(picture)

            profile_instance.save()
            # 2. Add the success message
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("users:profile", user_id=user_id)

        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)
