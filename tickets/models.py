import uuid
import secrets
from django.db import models
from events.models import Event


class TicketType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_total = models.IntegerField()
    quantity_sold = models.IntegerField(default=0)
    sale_start = models.DateTimeField()
    sale_end = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sale_start", "name"]

    def __str__(self) -> str:
        return f"{self.name} - {self.event.title}"

    @property
    def quantity_available(self) -> int:
        """Return the number of tickets still available."""
        return max(0, self.quantity_total - self.quantity_sold)

    @property
    def is_on_sale(self) -> bool:
        """Check if tickets are currently on sale."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active
            and self.sale_start <= now <= self.sale_end
            and self.quantity_available > 0
        )


class Ticket(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name="tickets")
    code = models.CharField(max_length=150, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Ticket {self.code} ({self.status})"

    @classmethod
    def generate_unique_code(cls) -> str:
        """Generate a unique ticket code."""
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate a 12-character alphanumeric code
            code = secrets.token_urlsafe(9).upper().replace("-", "").replace("_", "")[:12]
            if not cls.objects.filter(code=code).exists():
                return code
        raise ValueError("Unable to generate unique ticket code after multiple attempts")


