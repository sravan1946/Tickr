from django.urls import path

from . import views

app_name = "tickets"

# URL paths match tickr.md: PUT/DELETE /tickets/types/<id>/, GET /tickets/<code>/
# GET/POST /events/<id>/tickets/ is handled in main urlconf
urlpatterns = [
    path("types/<uuid:pk>/", views.TicketTypeUpdateView.as_view(), name="ticket_type_update"),
    path("types/<uuid:pk>/delete/", views.TicketTypeDeleteView.as_view(), name="ticket_type_delete"),
    path("<str:code>/", views.TicketDetailView.as_view(), name="ticket_detail"),
]
