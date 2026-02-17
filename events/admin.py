from django.contrib import admin

from .models import EventCategory, Venue, Event, EventImage


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "capacity")
    search_fields = ("name", "city")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "category", "venue", "start_date", "end_date", "capacity", "is_published")
    list_filter = ("is_published", "is_cancelled", "category", "venue")
    search_fields = ("title", "description")
    raw_id_fields = ("organizer",)


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ("event", "is_primary")
    list_filter = ("is_primary", "event")
