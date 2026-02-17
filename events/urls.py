from django.urls import path
from tickets.views import TicketTypeListView

from . import views

app_name = "events"

# URL paths match tickr.md: GET/POST /events/, GET /events/<slug>/, PUT/DELETE /events/<id>/, GET/POST /events/<id>/sessions/
# GET /categories/ and GET /venues/ are mounted at root in main urlconf.
urlpatterns = [
    path("", views.EventListView.as_view(), name="event_list"),
    path("create/", views.EventCreateView.as_view(), name="event_create"),
    path("<slug:slug>/", views.EventDetailView.as_view(), name="event_detail"),
    path("<uuid:pk>/edit/", views.EventUpdateView.as_view(), name="event_edit"),
    path("<uuid:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
    path("<uuid:pk>/tickets/", TicketTypeListView.as_view(), name="event_tickets"),
]
