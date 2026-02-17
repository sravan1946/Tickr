from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator

from accounts.auth import get_request_user
from accounts.models import OrganizerProfile
from accounts.views import login_required, organizer_required
from events.models import Event

from .models import PromoCode
from .forms import PromoCodeForm, PromoCodeValidateForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_organizer_profile(request: HttpRequest) -> OrganizerProfile | None:
    """Return OrganizerProfile for current user or None."""
    user = get_request_user(request)
    if not user or not getattr(user, "is_organizer", False):
        return None
    try:
        return user.organizer_profile
    except Exception:
        return None


def _promo_owned_by_user(request: HttpRequest, promo: PromoCode) -> bool:
    """Return True if the current user's organizer profile owns the promo's event."""
    profile = _get_organizer_profile(request)
    return profile is not None and promo.event.organizer_id == profile.pk


# ---------------------------------------------------------------------------
# POST /promocodes/ — create a promo code
# ---------------------------------------------------------------------------

class PromoCodeCreateView(View):
    """
    GET : show create form (requires ?event=<uuid>).
    POST: create PromoCode linked to the event.
    """

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        event_id = request.GET.get("event")
        if not event_id:
            messages.error(request, "Please select an event first.")
            return redirect("events:event_list")

        event = get_object_or_404(Event, pk=event_id)
        profile = _get_organizer_profile(request)
        if not profile or event.organizer_id != profile.pk:
            messages.error(request, "You can only manage promo codes for your own events.")
            return redirect("events:event_list")

        form = PromoCodeForm()
        return render(request, "promotions/promocode_form.html", {
            "form": form,
            "event": event,
        })

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest) -> HttpResponse:
        event_id = request.POST.get("event_id")
        if not event_id:
            messages.error(request, "Missing event.")
            return redirect("events:event_list")

        event = get_object_or_404(Event, pk=event_id)
        profile = _get_organizer_profile(request)
        if not profile or event.organizer_id != profile.pk:
            messages.error(request, "You can only manage promo codes for your own events.")
            return redirect("events:event_list")

        form = PromoCodeForm(request.POST)
        if not form.is_valid():
            return render(request, "promotions/promocode_form.html", {
                "form": form,
                "event": event,
            }, status=400)

        promo = form.save(commit=False)
        promo.event = event
        promo.save()
        messages.success(request, f"Promo code '{promo.code}' created.")
        return redirect("event_promocode_list", pk=event.pk)


# ---------------------------------------------------------------------------
# PUT /promocodes/<id>/ — update a promo code
# ---------------------------------------------------------------------------

class PromoCodeUpdateView(View):
    """GET: show edit form.  POST: save changes."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        promo = get_object_or_404(PromoCode, pk=pk)
        if not _promo_owned_by_user(request, promo):
            messages.error(request, "You can only edit your own promo codes.")
            return redirect("events:event_list")

        form = PromoCodeForm(instance=promo)
        return render(request, "promotions/promocode_form.html", {
            "form": form,
            "event": promo.event,
            "promo": promo,
        })

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        promo = get_object_or_404(PromoCode, pk=pk)
        if not _promo_owned_by_user(request, promo):
            messages.error(request, "You can only edit your own promo codes.")
            return redirect("events:event_list")

        form = PromoCodeForm(request.POST, instance=promo)
        if not form.is_valid():
            return render(request, "promotions/promocode_form.html", {
                "form": form,
                "event": promo.event,
                "promo": promo,
            }, status=400)

        form.save()
        messages.success(request, f"Promo code '{promo.code}' updated.")
        return redirect("event_promocode_list", pk=promo.event.pk)


# ---------------------------------------------------------------------------
# DELETE /promocodes/<id>/ — delete a promo code
# ---------------------------------------------------------------------------

class PromoCodeDeleteView(View):
    """GET: confirm delete.  POST: delete."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        promo = get_object_or_404(PromoCode, pk=pk)
        if not _promo_owned_by_user(request, promo):
            messages.error(request, "You can only delete your own promo codes.")
            return redirect("events:event_list")

        return render(request, "promotions/promocode_confirm_delete.html", {
            "promo": promo,
            "event": promo.event,
        })

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        promo = get_object_or_404(PromoCode, pk=pk)
        if not _promo_owned_by_user(request, promo):
            messages.error(request, "You can only delete your own promo codes.")
            return redirect("events:event_list")

        event_pk = promo.event.pk
        promo.delete()
        messages.success(request, "Promo code deleted.")
        return redirect("event_promocode_list", pk=event_pk)


# ---------------------------------------------------------------------------
# POST /promocodes/validate/ — validate a promo code
# ---------------------------------------------------------------------------

class PromoCodeValidateView(View):
    """
    POST: validate a promo code for a given event.
    Returns JSON for AJAX or redirects for regular form submissions.
    """

    @method_decorator(login_required)
    def post(self, request: HttpRequest) -> HttpResponse:
        form = PromoCodeValidateForm(request.POST)
        if not form.is_valid():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"valid": False, "error": "Invalid input."}, status=400)
            messages.error(request, "Invalid input.")
            return redirect("events:event_list")

        code = form.cleaned_data["code"].upper()
        event_id = form.cleaned_data["event_id"]

        try:
            promo = PromoCode.objects.get(code=code, event_id=event_id)
        except PromoCode.DoesNotExist:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"valid": False, "error": "Promo code not found."})
            messages.error(request, "Promo code not found.")
            return redirect(f"/orders/?event={event_id}")

        if not promo.is_valid:
            reason = "Promo code is expired or has reached its usage limit."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"valid": False, "error": reason})
            messages.error(request, reason)
            return redirect(f"/orders/?event={event_id}")

        data = {
            "valid": True,
            "code": promo.code,
            "discount_type": promo.discount_type,
            "discount_value": str(promo.discount_value),
        }
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(data)

        messages.success(request, f"Promo code '{promo.code}' is valid! {promo.discount_value}{'%' if promo.discount_type == 'percentage' else ' flat'} discount.")
        return redirect(f"/orders/?event={event_id}")


# ---------------------------------------------------------------------------
# GET /events/<id>/promocodes/ — list promo codes for an event
# ---------------------------------------------------------------------------

class EventPromoCodeListView(View):
    """List all promo codes for an event (organizer only)."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        event = get_object_or_404(Event, pk=pk)
        profile = _get_organizer_profile(request)
        if not profile or event.organizer_id != profile.pk:
            messages.error(request, "You can only view promo codes for your own events.")
            return redirect("events:event_list")

        promo_codes = event.promo_codes.all()
        return render(request, "promotions/promocode_list.html", {
            "event": event,
            "promo_codes": promo_codes,
        })
