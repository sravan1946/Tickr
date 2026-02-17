from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator

from accounts.auth import get_request_user
from core.decorators import organizer_required
from core.helpers import get_organizer_profile, event_owned_by_user
from events.models import Event
from tickets.models import Ticket

from .models import CheckIn
from .forms import CheckInForm


# ---------------------------------------------------------------------------
# GET/POST /checkin/<event_id>/ — scan / check-in a ticket
# ---------------------------------------------------------------------------

class CheckInScanView(View):
    """
    GET : show the check-in scan form for an event.
    POST: validate the ticket code and record a check-in.
    """

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only check in tickets for your own events.")
            return redirect("events:event_list")

        total_tickets = Ticket.objects.filter(
            ticket_type__event=event, status="booked"
        ).count()
        checked_in_count = CheckIn.objects.filter(
            ticket__ticket_type__event=event
        ).count()

        return render(request, "checkin/checkin_scan.html", {
            "event": event,
            "form": CheckInForm(),
            "total_tickets": total_tickets,
            "checked_in_count": checked_in_count,
        })

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only check in tickets for your own events.")
            return redirect("events:event_list")

        form = CheckInForm(request.POST)
        if not form.is_valid():
            return render(request, "checkin/checkin_scan.html", {
                "event": event,
                "form": form,
            }, status=400)

        code = form.cleaned_data["code"].strip()
        user = get_request_user(request)

        # Look up the ticket
        try:
            ticket = Ticket.objects.select_related("ticket_type__event").get(code=code)
        except Ticket.DoesNotExist:
            return render(request, "checkin/checkin_result.html", {
                "event": event,
                "success": False,
                "error": f"No ticket found with code '{code}'.",
                "form": CheckInForm(),
            })

        # Validate ticket belongs to this event
        if ticket.ticket_type.event_id != event.pk:
            return render(request, "checkin/checkin_result.html", {
                "event": event,
                "success": False,
                "error": f"Ticket '{code}' does not belong to this event.",
                "form": CheckInForm(),
            })

        # Validate ticket is booked
        if ticket.status != "booked":
            return render(request, "checkin/checkin_result.html", {
                "event": event,
                "success": False,
                "error": f"Ticket '{code}' has status '{ticket.status}' — only booked tickets can be checked in.",
                "form": CheckInForm(),
            })

        # Check if already checked in
        if hasattr(ticket, "checkin"):
            return render(request, "checkin/checkin_result.html", {
                "event": event,
                "success": False,
                "error": f"Ticket '{code}' has already been checked in at {ticket.checkin.checked_in_at:%Y-%m-%d %H:%M}.",
                "form": CheckInForm(),
                "ticket": ticket,
            })

        # Perform check-in
        checkin = CheckIn.objects.create(ticket=ticket, checked_in_by=user)

        # Try to get attendee info
        attendee = None
        try:
            attendee = ticket.attendee
        except Exception:
            pass

        return render(request, "checkin/checkin_result.html", {
            "event": event,
            "success": True,
            "checkin": checkin,
            "ticket": ticket,
            "attendee": attendee,
            "form": CheckInForm(),
        })


# ---------------------------------------------------------------------------
# GET /checkin/<event_id>/list/ — list all check-ins for an event
# ---------------------------------------------------------------------------

class CheckInListView(View):
    """List all check-ins for an event with stats (organizer only)."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only view check-ins for your own events.")
            return redirect("events:event_list")

        checkins = (
            CheckIn.objects
            .filter(ticket__ticket_type__event=event)
            .select_related("ticket", "ticket__ticket_type", "checked_in_by")
            .order_by("-checked_in_at")
        )

        total_tickets = Ticket.objects.filter(
            ticket_type__event=event, status="booked"
        ).count()
        checked_in_count = checkins.count()

        return render(request, "checkin/checkin_list.html", {
            "event": event,
            "checkins": checkins,
            "total_tickets": total_tickets,
            "checked_in_count": checked_in_count,
        })
