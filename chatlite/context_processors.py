def sidebar_context(request):
    context = {}
    if request.user.is_authenticated:
        context["channels"] = request.user.member_of.all()
    return context


def htmx_context(request):
    return {"is_htmx_request": request.headers.get("HX-Request") == "true"}
