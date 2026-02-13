import uuid
from django.db import models
from accounts.models import OrganizerProfile

# Create your models here.
class EventCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=150)
    capacity = models.IntegerField()

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.CASCADE, related_name="events")
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name="events")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class EventSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class EventImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="event_images/")
    is_primary = models.BooleanField(default=False)
