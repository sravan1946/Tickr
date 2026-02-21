"""
core.helpers — Shared ownership-check utilities.

Centralised here so every app can import from one place instead of
duplicating these private functions in each views.py.
"""

from django.http import HttpRequest

from accounts.auth import get_request_user
from accounts.models import OrganizerProfile
from events.models import Event
from tickets.models import TicketType


def get_organizer_profile(request: HttpRequest) -> OrganizerProfile | None:
    """Return the OrganizerProfile for the current session user, or None."""
    user = get_request_user(request)
    if not user or not getattr(user, "is_organizer", False):
        return None
    try:
        return user.organizer_profile
    except OrganizerProfile.DoesNotExist:
        return None


def event_owned_by_user(request: HttpRequest, event: Event) -> bool:
    """Return True if the logged-in organizer owns *event*."""
    profile = get_organizer_profile(request)
    return profile is not None and event.organizer_id == profile.pk


def ticket_type_owned_by_user(request: HttpRequest, ticket_type: TicketType) -> bool:
    """Return True if the logged-in organizer owns the ticket type's event."""
    return event_owned_by_user(request, ticket_type.event)


def promo_owned_by_user(request: HttpRequest, promo: object) -> bool:
    """Return True if the logged-in organizer owns the promo code's event."""
    return event_owned_by_user(request, promo.event)  # type: ignore[arg-type]
