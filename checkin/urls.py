from django.urls import path

from . import views

app_name = "checkin"

urlpatterns = [
    path("<uuid:pk>/", views.CheckInScanView.as_view(), name="checkin_scan"),
    path("<uuid:pk>/list/", views.CheckInListView.as_view(), name="checkin_list"),
]
