from django.http import HttpRequest

from .auth import get_request_user


def account_user(request: HttpRequest) -> dict[str, object]:
    """Add account_user to template context for session-based auth."""
    return {"account_user": get_request_user(request)}
