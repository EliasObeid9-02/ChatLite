from django.shortcuts import redirect


class HtmxMixin:
    """
    Mixin to add HTMX-specific context variables to a view.
    """

    def is_htmx_request(self):
        return self.request.headers.get("HX-Request") == "true"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_htmx_request"] = self.is_htmx_request()
        return context


class RedirectIfAuthenticatedMixin:
    """
    A mixin that redirects an already authenticated user to the home page.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("chats:home")
        return super().dispatch(request, *args, **kwargs)
