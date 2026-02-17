"""
URL configuration for tickr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from accounts.views import OrganizerProfileView
from core.views import HomeView
from events.views import CategoryListView, VenueListView
from orders.views import MyOrdersView
from promotions.views import EventPromoCodeListView

# URL structure matches tickr.md §4 API Endpoints.
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("organizer/profile/", OrganizerProfileView.as_view(), name="organizer_profile"),
    path("events/", include("events.urls")),
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("venues/", VenueListView.as_view(), name="venue_list"),
    path("tickets/", include("tickets.urls")),
    path("orders/", include("orders.urls")),
    path("my/orders/", MyOrdersView.as_view(), name="my_orders"),
    path("promocodes/", include("promotions.urls")),
    path("events/<uuid:pk>/promocodes/", EventPromoCodeListView.as_view(), name="event_promocode_list"),
    path("checkin/", include("checkin.urls")),
]
