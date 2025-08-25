from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("users.urls", namespace="users")),
    path("", include("chats.urls", namespace="chats")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
