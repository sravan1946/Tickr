from django.contrib import admin

from .models import Attendee, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("id", "price_per_ticket")


class AttendeeInline(admin.TabularInline):
    model = Attendee
    extra = 0
    readonly_fields = ("id", "ticket")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "event", "total_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "user__username", "event__title")
    readonly_fields = ("id", "created_at")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "ticket_type", "quantity", "price_per_ticket")
    search_fields = ("order__user__email", "ticket_type__name")
    readonly_fields = ("id",)
    inlines = [AttendeeInline]


@admin.register(Attendee)
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "order_item", "ticket")
    search_fields = ("full_name", "email")
    readonly_fields = ("id",)
