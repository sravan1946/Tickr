from django.contrib import admin

from .models import CheckIn


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("ticket", "checked_in_at", "checked_in_by")
    search_fields = ("ticket__code",)
    list_filter = ("checked_in_at",)
    readonly_fields = ("id", "checked_in_at")
