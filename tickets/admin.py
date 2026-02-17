from django.contrib import admin
from .models import TicketType, Ticket


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "price", "quantity_total", "quantity_sold", "is_active", "sale_start", "sale_end")
    list_filter = ("is_active", "sale_start", "sale_end")
    search_fields = ("name", "event__title")
    readonly_fields = ("id", "created_at", "quantity_sold")
    date_hierarchy = "sale_start"


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("code", "ticket_type", "status", "created_at")
    list_filter = ("status", "created_at", "ticket_type__event")
    search_fields = ("code", "ticket_type__name", "ticket_type__event__title")
    readonly_fields = ("id", "created_at")
    date_hierarchy = "created_at"
