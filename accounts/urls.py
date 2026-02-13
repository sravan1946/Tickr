from django.urls import path, include
from . import views

app_name = "accounts"

auth_patterns = [
    path('login/', views.LoginView.as_view(), name='login_view'),
    path('logout/', views.LogoutView.as_view(), name='logout_view'),
    path('register/', views.RegisterView.as_view(), name='register_view'),
    path('me/', views.MeView.as_view(), name='me_view'),
]

organizer_patterns = [
    path('profile/', views.OrganizerProfileView.as_view(), name='organizer_profile_view'),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('organizer/', include(organizer_patterns)),
]
