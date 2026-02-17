from django.urls import path

from . import views

app_name = "orders"

# URL paths match tickr.md §4: POST /orders/, GET /orders/<id>/, etc.
urlpatterns = [
    path("", views.OrderCreateView.as_view(), name="order_create"),
    path("<uuid:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("<uuid:pk>/confirm/", views.OrderConfirmView.as_view(), name="order_confirm"),
    path("<uuid:pk>/cancel/", views.OrderCancelView.as_view(), name="order_cancel"),
    path("<uuid:pk>/attendees/", views.AttendeeCreateView.as_view(), name="order_attendees"),
]
