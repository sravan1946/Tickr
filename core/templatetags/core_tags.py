"""
core.templatetags.core_tags — Shared template tags & filters.

Usage in templates:
    {% load core_tags %}
    <a href="?{% query_string page=2 %}">Next</a>
"""
from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """
    Build a query-string from the current request's GET parameters,
    overriding any keys supplied as keyword arguments.

    Example:
        {% query_string page=3 %}          → preserves existing GET params, sets page=3
        {% query_string page=3 sort=name %} → sets page=3 and sort=name
    """
    request = context.get("request")
    if request is None:
        return urlencode(kwargs)
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return params.urlencode()
