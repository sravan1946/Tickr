"""
core.decorators — Shared view decorators for authentication & authorisation.

Moved from accounts.views so that every app can import without depending
on accounts' view layer.
"""
import functools
from typing import Callable, TypeVar

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, resolve_url
from django.contrib import messages
from django.utils.http import urlencode

from accounts.auth import get_request_user

F = TypeVar("F", bound=Callable[..., HttpResponse])


def login_required(f: F) -> F:
    """Decorator: redirect to login if no session user."""
    @functools.wraps(f)
    def wrapped(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if get_request_user(request) is None:
            messages.warning(request, "Please log in to continue.")
            login_url = resolve_url("accounts:login")
            next_url = request.get_full_path()
            return redirect(f"{login_url}?{urlencode({'next': next_url})}")
        return f(request, *args, **kwargs)
    return wrapped  # type: ignore[return-value]


def organizer_required(f: F) -> F:
    """Decorator: redirect if user is not an organizer."""
    @functools.wraps(f)
    def wrapped(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        user = get_request_user(request)
        if user is None:
            messages.warning(request, "Please log in to continue.")
            login_url = resolve_url("accounts:login")
            next_url = request.get_full_path()
            return redirect(f"{login_url}?{urlencode({'next': next_url})}")
        if not getattr(user, "is_organizer", False):
            messages.error(request, "Organizer access required.")
            return redirect("accounts:me")
        return f(request, *args, **kwargs)
    return wrapped  # type: ignore[return-value]
