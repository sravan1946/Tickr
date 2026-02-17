from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator

from accounts.models import OrganizerProfile
from accounts.views import organizer_required
from accounts.auth import get_request_user
from events.models import Event

from .models import TicketType, Ticket
from .forms import TicketTypeForm


def _get_organizer_profile(request: HttpRequest) -> OrganizerProfile | None:
    """Return OrganizerProfile for current user or None."""
    user = get_request_user(request)
    if not user or not getattr(user, "is_organizer", False):
        return None
    try:
        return user.organizer_profile
    except Exception:
        return None


def _event_owned_by_user(request: HttpRequest, event: Event) -> bool:
    """Return True if the current user's organizer profile owns this event."""
    profile = _get_organizer_profile(request)
    return profile is not None and event.organizer_id == profile.pk


def _ticket_type_owned_by_user(request: HttpRequest, ticket_type: TicketType) -> bool:
    """Return True if the current user's organizer profile owns the ticket type's event."""
    return _event_owned_by_user(request, ticket_type.event)


class TicketTypeListView(View):
    """GET /events/<id>/tickets/ — list ticket types for an event."""

    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        ticket_types = event.ticket_types.all()
        is_owner = _event_owned_by_user(request, event)

        # Only show unpublished events to owners
        if not event.is_published and not is_owner:
            messages.error(request, "Event not found.")
            return redirect("events:event_list")

        return render(
            request,
            "tickets/ticket_type_list.html",
            {
                "event": event,
                "ticket_types": ticket_types,
                "is_owner": is_owner,
                "form": TicketTypeForm() if is_owner else None,
            },
        )

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        """POST /events/<id>/tickets/ — create ticket type (organizer only, must own event)."""
        event = get_object_or_404(Event, pk=pk)
        if not _event_owned_by_user(request, event):
            messages.error(request, "You can only create ticket types for your own events.")
            return redirect("events:event_detail", slug=event.slug)

        form = TicketTypeForm(request.POST)
        if not form.is_valid():
            ticket_types = event.ticket_types.all()
            return render(
                request,
                "tickets/ticket_type_list.html",
                {
                    "event": event,
                    "ticket_types": ticket_types,
                    "is_owner": True,
                    "form": form,
                },
                status=400,
            )

        ticket_type = form.save(commit=False)
        ticket_type.event = event
        ticket_type.save()
        messages.success(request, "Ticket type created.")
        return redirect("events:event_tickets", pk=event.pk)


class TicketTypeUpdateView(View):
    """GET/POST /tickets/types/<id>/ — update ticket type (organizer only, must own event)."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        ticket_type = get_object_or_404(TicketType, pk=pk)
        if not _ticket_type_owned_by_user(request, ticket_type):
            messages.error(request, "You can only edit ticket types for your own events.")
            return redirect("events:event_list")

        form = TicketTypeForm(instance=ticket_type)
        return render(
            request,
            "tickets/ticket_type_form.html",
            {"form": form, "ticket_type": ticket_type, "event": ticket_type.event},
        )

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        ticket_type = get_object_or_404(TicketType, pk=pk)
        if not _ticket_type_owned_by_user(request, ticket_type):
            messages.error(request, "You can only edit ticket types for your own events.")
            return redirect("events:event_list")

        form = TicketTypeForm(request.POST, instance=ticket_type)
        if not form.is_valid():
            return render(
                request,
                "tickets/ticket_type_form.html",
                {"form": form, "ticket_type": ticket_type, "event": ticket_type.event},
                status=400,
            )

        form.save()
        messages.success(request, "Ticket type updated.")
        return redirect("events:event_tickets", pk=ticket_type.event.pk)


class TicketTypeDeleteView(View):
    """GET/POST /tickets/types/<id>/delete/ — delete ticket type (organizer only, must own event)."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        ticket_type = get_object_or_404(TicketType, pk=pk)
        if not _ticket_type_owned_by_user(request, ticket_type):
            messages.error(request, "You can only delete ticket types for your own events.")
            return redirect("events:event_list")

        return render(
            request,
            "tickets/ticket_type_confirm_delete.html",
            {"ticket_type": ticket_type, "event": ticket_type.event},
        )

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        ticket_type = get_object_or_404(TicketType, pk=pk)
        if not _ticket_type_owned_by_user(request, ticket_type):
            messages.error(request, "You can only delete ticket types for your own events.")
            return redirect("events:event_list")

        event_pk = ticket_type.event.pk
        ticket_type.delete()
        messages.success(request, "Ticket type deleted.")
        return redirect("events:event_tickets", pk=event_pk)


class TicketDetailView(View):
    """GET /tickets/<code>/ — get ticket details by code."""

    def get(self, request: HttpRequest, code: str) -> HttpResponse:
        ticket = get_object_or_404(Ticket, code=code)
        event = ticket.ticket_type.event
        is_owner = _event_owned_by_user(request, event)

        return render(
            request,
            "tickets/ticket_detail.html",
            {
                "ticket": ticket,
                "ticket_type": ticket.ticket_type,
                "event": event,
                "is_owner": is_owner,
            },
        )
