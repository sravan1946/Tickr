import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from events.models import Event


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("flat", "Flat"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="promo_codes")
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "code"]

    def __str__(self) -> str:
        return f"{self.code} ({self.event.title})"

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    @property
    def is_valid(self) -> bool:
        """Check if this promo code can still be used."""
        if not self.is_active:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        if self.expires_at and timezone.now() >= self.expires_at:
            return False
        return True

    def apply_discount(self, amount: Decimal) -> Decimal:
        """Return the discounted amount (never below 0)."""
        if self.discount_type == "percentage":
            discount = amount * (self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value
        return max(amount - discount, Decimal("0"))
