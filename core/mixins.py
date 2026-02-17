"""
core.mixins — Class-based-view mixins for authentication & authorisation.

Usage:
    class MyView(LoginRequiredMixin, View):
        ...
"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib import messages

from accounts.auth import get_request_user


class LoginRequiredMixin:
    """Redirect to login if no session user (CBV mixin)."""

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if get_request_user(request) is None:
            messages.warning(request, "Please log in to continue.")
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]


class OrganizerRequiredMixin:
    """Redirect if user is not an organizer (CBV mixin)."""

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        user = get_request_user(request)
        if user is None:
            messages.warning(request, "Please log in to continue.")
            return redirect("accounts:login")
        if not getattr(user, "is_organizer", False):
            messages.error(request, "Organizer access required.")
            return redirect("accounts:me")
        return super().dispatch(request, *args, **kwargs)  # type: ignore[misc]
