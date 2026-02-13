from django.urls import path

from . import views

app_name = "accounts"

# Mounted at auth/ in root urlconf → /auth/login/, /auth/register/, etc.
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("me/", views.MeView.as_view(), name="me"),
]
