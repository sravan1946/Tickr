import uuid
from django.db import models
from accounts.models import User
from tickets.models import Ticket


class CheckIn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="checkin")
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="checkins_performed",
    )

    class Meta:
        ordering = ["-checked_in_at"]

    def __str__(self) -> str:
        return f"Check-in {self.ticket.code} at {self.checked_in_at:%Y-%m-%d %H:%M}"
