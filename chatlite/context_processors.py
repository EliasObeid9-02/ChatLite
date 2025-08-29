import re


def sidebar_context(request):
    context = {}
    if request.user.is_authenticated:
        context["channels"] = request.user.member_of.all()

        # Extract active channel ID from the request path
        match = re.search(r"channel/([0-9a-f-]+)/", request.path)
        active_channel_id = match.group(1) if match else None
        context["active_channel_id"] = active_channel_id
    return context


def htmx_context(request):
    return {"is_htmx_request": request.headers.get("HX-Request") == "true"}
