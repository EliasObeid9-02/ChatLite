from django.contrib import admin
from django.urls import include, path

from users.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls", namespace="users")),
    path("", include("chats.urls", namespace="chats")),
    path("", HomeView.as_view(), name="home"),
]
