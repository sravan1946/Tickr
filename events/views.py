from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator

from accounts.models import OrganizerProfile
from accounts.views import organizer_required
from accounts.auth import get_request_user

from .models import Event, EventCategory, Venue
from .forms import EventForm


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


class EventListView(View):
    """GET /events/ — list. POST /events/ — create (organizer only, per spec)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        events = Event.objects.filter(is_published=True, is_cancelled=False).order_by(
            "-start_date"
        )
        organizer_profile = _get_organizer_profile(request)
        my_events: list[Event] = []
        if organizer_profile:
            my_events = list(
                Event.objects.filter(organizer=organizer_profile).order_by("-created_at")
            )
        return render(
            request,
            "events/event_list.html",
            {
                "events": events,
                "my_events": my_events,
                "is_organizer": organizer_profile is not None,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        """POST /events/ — create event (organizer only)."""
        organizer_profile = _get_organizer_profile(request)
        if not organizer_profile:
            messages.error(request, "Organizer access required.")
            return redirect("events:event_list")
        form = EventForm(request.POST)
        if not form.is_valid():
            return render(request, "events/event_form.html", {"form": form}, status=400)
        event = form.save(commit=False)
        event.organizer = organizer_profile
        event.save()
        messages.success(request, "Event created.")
        return redirect("events:event_detail", slug=event.slug)


class EventDetailView(View):
    """GET /events/<slug>/ — event detail (public if published, else 404 or owner-only)."""

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        event = get_object_or_404(Event, slug=slug)
        is_owner = _event_owned_by_user(request, event)
        if not event.is_published and not is_owner:
            return redirect("events:event_list")
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "is_owner": is_owner},
        )


class EventCreateView(View):
    """GET /events/create/ — show create form (organizer only). Form posts to POST /events/."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "events/event_form.html", {"form": EventForm()})


class EventUpdateView(View):
    """GET/POST /events/<id>/edit/ — organizer only, must own event."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not _event_owned_by_user(request, event):
            messages.error(request, "You can only edit your own events.")
            return redirect("events:event_list")
        form = EventForm(instance=event)
        return render(request, "events/event_form.html", {"form": form, "event": event})

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not _event_owned_by_user(request, event):
            messages.error(request, "You can only edit your own events.")
            return redirect("events:event_list")
        form = EventForm(request.POST, instance=event)
        if not form.is_valid():
            return render(
                request,
                "events/event_form.html",
                {"form": form, "event": event},
                status=400,
            )
        form.save()
        messages.success(request, "Event updated.")
        return redirect("events:event_detail", slug=event.slug)


class EventDeleteView(View):
    """GET/POST /events/<id>/delete/ — organizer only, must own event."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not _event_owned_by_user(request, event):
            messages.error(request, "You can only delete your own events.")
            return redirect("events:event_list")
        return render(request, "events/event_confirm_delete.html", {"event": event})

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not _event_owned_by_user(request, event):
            messages.error(request, "You can only delete your own events.")
            return redirect("events:event_list")
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect("events:event_list")


class CategoryListView(View):
    """GET /categories/ — list categories."""

    def get(self, request: HttpRequest) -> HttpResponse:
        categories = EventCategory.objects.order_by("name")
        return render(request, "events/category_list.html", {"categories": categories})


class VenueListView(View):
    """GET /venues/ — list venues."""

    def get(self, request: HttpRequest) -> HttpResponse:
        venues = Venue.objects.order_by("city", "name")
        return render(request, "events/venue_list.html", {"venues": venues})
