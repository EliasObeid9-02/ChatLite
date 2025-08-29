from django.shortcuts import redirect





class RedirectIfAuthenticatedMixin:
    """
    A mixin that redirects an already authenticated user to the home page.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("chats:home")
        return super().dispatch(request, *args, **kwargs)
