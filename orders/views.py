from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db import transaction

from accounts.auth import get_request_user
from core.decorators import login_required
from events.models import Event
from tickets.models import TicketType, Ticket
from promotions.models import PromoCode

from .models import Order, OrderItem, Attendee
from .forms import OrderTicketForm, AttendeeForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_or_redirect(request: HttpRequest):
    """Return the logged-in user or None (callers should redirect)."""
    return get_request_user(request)


# ---------------------------------------------------------------------------
# POST /orders/ — create a new order
# ---------------------------------------------------------------------------

class OrderCreateView(View):
    """
    GET : show ticket selection form for a given event (?event=<uuid>).
    POST: create Order + OrderItems from selected quantities.
    """

    @method_decorator(login_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        event_id = request.GET.get("event")
        if not event_id:
            messages.error(request, "Please select an event first.")
            return redirect("events:event_list")
        event = get_object_or_404(Event, pk=event_id, is_published=True, is_cancelled=False)
        ticket_types = event.ticket_types.filter(is_active=True)

        forms = []
        for tt in ticket_types:
            forms.append({
                "ticket_type": tt,
                "form": OrderTicketForm(initial={"ticket_type_id": tt.pk}),
            })

        return render(request, "orders/order_create.html", {
            "event": event,
            "ticket_forms": forms,
            "has_promo_codes": event.promo_codes.filter(is_active=True).exists(),
        })

    @method_decorator(login_required)
    def post(self, request: HttpRequest) -> HttpResponse:
        event_id = request.POST.get("event_id")
        if not event_id:
            messages.error(request, "Missing event.")
            return redirect("events:event_list")

        event = get_object_or_404(Event, pk=event_id, is_published=True, is_cancelled=False)
        user = _get_user_or_redirect(request)

        # Parse all ticket-type / quantity pairs from the POST body.
        # Each row sends ticket_type_id + quantity with a prefix like row-<n>-
        ticket_type_ids = request.POST.getlist("ticket_type_id")
        quantities_raw = request.POST.getlist("quantity")

        if len(ticket_type_ids) != len(quantities_raw):
            messages.error(request, "Invalid form data.")
            return redirect("orders:order_create")

        # Build items list — skip rows where quantity == 0
        items_to_create = []
        for tt_id, qty_str in zip(ticket_type_ids, quantities_raw):
            try:
                qty = int(qty_str)
            except (ValueError, TypeError):
                qty = 0
            if qty <= 0:
                continue
            tt = TicketType.objects.filter(pk=tt_id, event=event, is_active=True).first()
            if tt is None:
                messages.error(request, "Invalid ticket type selected.")
                return redirect("orders:order_create")
            if qty > tt.quantity_available:
                messages.error(
                    request,
                    f"Only {tt.quantity_available} tickets available for '{tt.name}'.",
                )
                return redirect(f"/orders/?event={event.pk}")
            items_to_create.append((tt, qty))

        if not items_to_create:
            messages.error(request, "Select at least one ticket.")
            return redirect(f"/orders/?event={event.pk}")

        # Validate optional promo code
        promo = None
        promo_code_str = request.POST.get("promo_code", "").strip().upper()
        if promo_code_str:
            try:
                promo = PromoCode.objects.get(code=promo_code_str, event=event)
                if not promo.is_valid:
                    messages.warning(request, "Promo code is expired or has reached its usage limit.")
                    promo = None
            except PromoCode.DoesNotExist:
                messages.warning(request, "Invalid promo code — ignored.")

        # Create Order + OrderItems atomically
        with transaction.atomic():
            order = Order.objects.create(user=user, event=event, promo_code=promo)
            for tt, qty in items_to_create:
                OrderItem.objects.create(
                    order=order,
                    ticket_type=tt,
                    quantity=qty,
                    price_per_ticket=tt.price,
                )
            order.recalculate_total()

            # Apply promo discount to total
            if promo:
                order.total_amount = promo.apply_discount(order.total_amount)
                order.save(update_fields=["total_amount"])

        if promo:
            messages.success(request, f"Order created with promo code '{promo.code}' applied!")
        else:
            messages.success(request, "Order created! Review and confirm below.")
        return redirect("orders:order_detail", pk=order.pk)


# ---------------------------------------------------------------------------
# GET /orders/<id>/ — view order
# ---------------------------------------------------------------------------

class OrderDetailView(View):
    """Display order details with items and attendees."""

    @method_decorator(login_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        user = _get_user_or_redirect(request)
        order = get_object_or_404(Order, pk=pk)

        # Only the order owner can view it
        if order.user_id != user.pk:
            messages.error(request, "You do not have access to this order.")
            return redirect("my_orders")

        items = order.items.select_related("ticket_type").all()
        # Prefetch attendees for each item
        for item in items:
            item.attendee_list = item.attendees.select_related("ticket").all()

        return render(request, "orders/order_detail.html", {
            "order": order,
            "items": items,
            "event": order.event,
        })


# ---------------------------------------------------------------------------
# POST /orders/<id>/confirm/ — confirm (pay) order
# ---------------------------------------------------------------------------

class OrderConfirmView(View):
    """Set order status to paid and issue Ticket objects."""

    @method_decorator(login_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        user = _get_user_or_redirect(request)
        order = get_object_or_404(Order, pk=pk)

        if order.user_id != user.pk:
            messages.error(request, "You do not have access to this order.")
            return redirect("my_orders")

        if order.status != "pending":
            messages.warning(request, f"Order is already {order.status}.")
            return redirect("orders:order_detail", pk=order.pk)

        with transaction.atomic():
            # Issue tickets for each item
            for item in order.items.select_related("ticket_type").all():
                tt = item.ticket_type
                if item.quantity > tt.quantity_available:
                    messages.error(
                        request,
                        f"Not enough tickets available for '{tt.name}'. Order cannot be confirmed.",
                    )
                    return redirect("orders:order_detail", pk=order.pk)

                for _ in range(item.quantity):
                    ticket = Ticket.objects.create(
                        ticket_type=tt,
                        code=Ticket.generate_unique_code(),
                        status="booked",
                    )
                    # If there is a matching attendee without a ticket, link it
                    unlinked = item.attendees.filter(ticket__isnull=True).first()
                    if unlinked:
                        unlinked.ticket = ticket
                        unlinked.save(update_fields=["ticket"])

                tt.quantity_sold += item.quantity
                tt.save(update_fields=["quantity_sold"])

            order.status = "paid"
            order.save(update_fields=["status"])

            # Increment promo code usage
            if order.promo_code:
                order.promo_code.used_count += 1
                order.promo_code.save(update_fields=["used_count"])

        messages.success(request, "Order confirmed! Your tickets have been issued.")
        return redirect("orders:order_detail", pk=order.pk)


# ---------------------------------------------------------------------------
# POST /orders/<id>/cancel/ — cancel order
# ---------------------------------------------------------------------------

class OrderCancelView(View):
    """Cancel an order and release any issued tickets."""

    @method_decorator(login_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        user = _get_user_or_redirect(request)
        order = get_object_or_404(Order, pk=pk)

        if order.user_id != user.pk:
            messages.error(request, "You do not have access to this order.")
            return redirect("my_orders")

        if order.status == "cancelled":
            messages.warning(request, "Order is already cancelled.")
            return redirect("orders:order_detail", pk=order.pk)

        with transaction.atomic():
            if order.status == "paid":
                # Release tickets
                for item in order.items.select_related("ticket_type").all():
                    for attendee in item.attendees.select_related("ticket").all():
                        if attendee.ticket:
                            attendee.ticket.status = "cancelled"
                            attendee.ticket.save(update_fields=["status"])
                    item.ticket_type.quantity_sold = max(
                        0, item.ticket_type.quantity_sold - item.quantity
                    )
                    item.ticket_type.save(update_fields=["quantity_sold"])

            order.status = "cancelled"
            order.save(update_fields=["status"])

        messages.success(request, "Order cancelled.")
        return redirect("orders:order_detail", pk=order.pk)


# ---------------------------------------------------------------------------
# GET /my/orders/ — list user's orders
# ---------------------------------------------------------------------------

class MyOrdersView(View):
    """List all orders for the current user."""

    @method_decorator(login_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        user = _get_user_or_redirect(request)
        orders = Order.objects.filter(user=user).select_related("event")
        return render(request, "orders/my_orders.html", {
            "orders": orders,
        })


# ---------------------------------------------------------------------------
# POST /orders/<id>/attendees/ — add attendee info
# ---------------------------------------------------------------------------

class AttendeeCreateView(View):
    """
    GET : show attendee forms for each OrderItem in the order.
    POST: save attendee records.
    """

    @method_decorator(login_required)
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        user = _get_user_or_redirect(request)
        order = get_object_or_404(Order, pk=pk)

        if order.user_id != user.pk:
            messages.error(request, "You do not have access to this order.")
            return redirect("my_orders")

        items_with_forms = []
        for item in order.items.select_related("ticket_type").all():
            existing = item.attendees.count()
            needed = item.quantity - existing
            forms = [AttendeeForm(prefix=f"att-{item.pk}-{i}") for i in range(needed)]
            items_with_forms.append({
                "item": item,
                "existing": item.attendees.all(),
                "forms": forms,
                "needed": needed,
            })

        return render(request, "orders/attendee_form.html", {
            "order": order,
            "items_with_forms": items_with_forms,
            "event": order.event,
        })

    @method_decorator(login_required)
    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        user = _get_user_or_redirect(request)
        order = get_object_or_404(Order, pk=pk)

        if order.user_id != user.pk:
            messages.error(request, "You do not have access to this order.")
            return redirect("my_orders")

        created_count = 0
        for item in order.items.select_related("ticket_type").all():
            existing = item.attendees.count()
            needed = item.quantity - existing
            for i in range(needed):
                form = AttendeeForm(request.POST, prefix=f"att-{item.pk}-{i}")
                if form.is_valid():
                    attendee = form.save(commit=False)
                    attendee.order_item = item
                    attendee.save()
                    created_count += 1

        if created_count:
            messages.success(request, f"{created_count} attendee(s) added.")
        else:
            messages.warning(request, "No attendees added. Check your input.")
        return redirect("orders:order_detail", pk=order.pk)
