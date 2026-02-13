from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="event_list"),
    path("create/", views.EventCreateView.as_view(), name="event_create"),
    path("<slug:slug>/", views.EventDetailView.as_view(), name="event_detail"),
    path("<uuid:pk>/edit/", views.EventUpdateView.as_view(), name="event_edit"),
    path("<uuid:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
    path("<uuid:pk>/sessions/", views.EventSessionListView.as_view(), name="event_sessions"),
    path(
        "<uuid:pk>/sessions/create/",
        views.EventSessionCreateView.as_view(),
        name="event_session_create",
    ),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("venues/", views.VenueListView.as_view(), name="venue_list"),
]
