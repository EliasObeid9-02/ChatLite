import re

def htmx_context(request):
    return {"is_htmx_request": request.headers.get("HX-Request") == "true"}

