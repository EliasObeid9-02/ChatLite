from django.urls import path

from users.views import LoginView, LogoutView, ProfileView, RegisterView

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/<uuid:user_id>/", ProfileView.as_view(), name="profile"),
]
