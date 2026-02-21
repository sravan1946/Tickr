from django.contrib import admin

from .models import OrganizerProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "is_organizer", "is_active", "created_at")
    list_filter = ("is_organizer", "is_active")
    search_fields = ("email", "username")
    readonly_fields = ("id", "created_at")


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "organization_name",
        "user",
        "contact_email",
        "verified",
        "created_at",
    )
    list_filter = ("verified",)
    search_fields = ("organization_name", "user__email", "contact_email")
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("user",)
