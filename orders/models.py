import uuid
from django.db import models
from accounts.models import User
from events.models import Event
from tickets.models import TicketType, Ticket


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.pk} — {self.user.email} — {self.status}"

    def recalculate_total(self) -> None:
        """Recalculate total_amount from items."""
        from django.db.models import F, Sum
        total = (
            self.items.aggregate(total=Sum(F("quantity") * F("price_per_ticket")))
            .get("total")
        ) or 0
        self.total_amount = total
        self.save(update_fields=["total_amount"])


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price_per_ticket = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quantity}× {self.ticket_type.name} @ ${self.price_per_ticket}"

    @property
    def subtotal(self):
        return self.quantity * self.price_per_ticket


class Attendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="attendees")
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendee",
    )

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"
