from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_uri(context, view_name, *args, **kwargs):
    """
    Custom template tag that takes a view name and its arguments
    and returns a full, absolute URL (including http/https and domain).
    """
    request = context.get("request")
    if not request:
        return ""

    relative_url = reverse(view_name, args=args, kwargs=kwargs)
    return request.build_absolute_uri(relative_url)
