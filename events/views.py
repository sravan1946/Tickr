from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from core.decorators import organizer_required
from core.helpers import event_owned_by_user, get_organizer_profile

from .forms import EventForm, EventImageForm
from .models import Event, EventCategory, EventImage, Venue


class EventListView(View):
    """GET /events/ — list. POST /events/ — create (organizer only, per spec)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        events = (
            Event.objects.filter(is_published=True, is_cancelled=False)
            .order_by("-start_date")
            .prefetch_related("ticket_types")
        )
        category = request.GET.get("category")
        if category:
            events = events.filter(category__name__iexact=category)
        organizer_profile = get_organizer_profile(request)
        my_events: list[Event] = []
        if organizer_profile:
            my_events_qs = (
                Event.objects.filter(organizer=organizer_profile)
                .order_by("-created_at")
                .prefetch_related("ticket_types")
            )
            if category:
                my_events_qs = my_events_qs.filter(category__name__iexact=category)
            my_events = list(my_events_qs)
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
        organizer_profile = get_organizer_profile(request)
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
        is_owner = event_owned_by_user(request, event)
        if not event.is_published and not is_owner:
            return redirect("events:event_list")
        has_tickets = event.ticket_types.filter(is_active=True).exists()
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "is_owner": is_owner, "has_tickets": has_tickets},
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
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only edit your own events.")
            return redirect("events:event_list")
        form = EventForm(instance=event)
        return render(request, "events/event_form.html", {"form": form, "event": event})

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
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
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only delete your own events.")
            return redirect("events:event_list")
        return render(request, "events/event_confirm_delete.html", {"event": event})

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
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


class EventImageListView(View):
    """GET /events/<id>/images/ — list images for an event."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only manage images for your own events.")
            return redirect("events:event_list")
        images = event.images.all()
        form = EventImageForm()
        return render(
            request,
            "events/event_images.html",
            {"event": event, "images": images, "form": form},
        )

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only manage images for your own events.")
            return redirect("events:event_list")
        form = EventImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(event=event)
            messages.success(request, "Image uploaded successfully.")
            return redirect("events:event_images", pk=event.pk)
        images = event.images.all()
        return render(
            request,
            "events/event_images.html",
            {"event": event, "images": images, "form": form},
            status=400,
        )


class EventImageDeleteView(View):
    """POST /events/<id>/images/<image_id>/delete/ — delete an image."""

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str, image_pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only delete images for your own events.")
            return redirect("events:event_list")
        image = get_object_or_404(EventImage, pk=image_pk, event=event)
        image.delete()
        messages.success(request, "Image deleted.")
        return redirect("events:event_images", pk=event.pk)


class EventImageSetPrimaryView(View):
    """POST /events/<id>/images/<image_id>/primary/ — set image as primary."""

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str, image_pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        if not event_owned_by_user(request, event):
            messages.error(request, "You can only manage images for your own events.")
            return redirect("events:event_list")
        image = get_object_or_404(EventImage, pk=image_pk, event=event)
        # Unset other primary images
        event.images.filter(is_primary=True).update(is_primary=False)
        # Set this one as primary
        image.is_primary = True
        image.save()
        messages.success(request, "Primary image updated.")
        return redirect("events:event_images", pk=event.pk)
