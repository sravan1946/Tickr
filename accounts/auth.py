"""
Session-based auth for custom User model.
Store user id in session; use get_request_user() in views.
"""
from django.http import HttpRequest

from .models import User

SESSION_USER_ID_KEY = "_tickr_user_id"


def get_request_user(request: HttpRequest) -> User | None:
    """Return the logged-in User or None."""
    if not request.session.get(SESSION_USER_ID_KEY):
        return None
    try:
        return User.objects.get(pk=request.session[SESSION_USER_ID_KEY])
    except User.DoesNotExist:
        request.session.flush()
        return None


def login_user(request: HttpRequest, user: User) -> None:
    """Log in a user by storing their id in the session."""
    request.session[SESSION_USER_ID_KEY] = str(user.pk)
    request.session.set_expiry(0)  # session cookie


def logout_user(request: HttpRequest) -> None:
    """Clear the session user."""
    request.session.pop(SESSION_USER_ID_KEY, None)
