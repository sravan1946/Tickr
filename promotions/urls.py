from django.urls import path

from . import views

app_name = "promotions"

# URL paths match tickr.md §4: POST /promocodes/, PUT/DELETE /promocodes/<id>/, POST /promocodes/validate/
# GET /events/<id>/promocodes/ is mounted separately in the main urlconf.
urlpatterns = [
    path("", views.PromoCodeCreateView.as_view(), name="promocode_create"),
    path("<uuid:pk>/", views.PromoCodeUpdateView.as_view(), name="promocode_update"),
    path("<uuid:pk>/delete/", views.PromoCodeDeleteView.as_view(), name="promocode_delete"),
    path("validate/", views.PromoCodeValidateView.as_view(), name="promocode_validate"),
]
