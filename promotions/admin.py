from django.contrib import admin

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "event",
        "discount_type",
        "discount_value",
        "used_count",
        "usage_limit",
        "is_active",
        "expires_at",
    )
    list_filter = ("is_active", "discount_type", "event")
    search_fields = ("code", "event__title")
    readonly_fields = ("id", "used_count")
