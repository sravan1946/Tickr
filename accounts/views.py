from typing import Callable, TypeVar

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.utils.decorators import method_decorator

from .models import User, OrganizerProfile
from .forms import LoginForm, RegisterForm, OrganizerProfileForm
from .auth import get_request_user, login_user, logout_user

F = TypeVar("F", bound=Callable[..., HttpResponse])


def login_required(f: F) -> F:
    """Decorator: redirect to login if no session user."""
    def wrapped(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if get_request_user(request) is None:
            messages.warning(request, "Please log in to continue.")
            return redirect("accounts:login")
        return f(request, *args, **kwargs)
    return wrapped  # type: ignore[return-value]


def organizer_required(f: F) -> F:
    """Decorator: redirect if user is not an organizer."""
    def wrapped(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        user = get_request_user(request)
        if user is None:
            messages.warning(request, "Please log in to continue.")
            return redirect("accounts:login")
        if not getattr(user, "is_organizer", False):
            messages.error(request, "Organizer access required.")
            return redirect("accounts:me")
        return f(request, *args, **kwargs)
    return wrapped  # type: ignore[return-value]


class LoginView(View):
    """GET: show login form. POST: authenticate and log in."""

    def get(self, request: HttpRequest) -> HttpResponse:
        if get_request_user(request):
            return redirect("accounts:me")
        return render(request, "accounts/login.html", {"form": LoginForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/login.html", {"form": form}, status=400)
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html", {"form": LoginForm(request.POST)})
        if not user.is_active:
            messages.error(request, "This account is inactive.")
            return render(request, "accounts/login.html", {"form": LoginForm(request.POST)})
        if not check_password(password, user.password):
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html", {"form": LoginForm(request.POST)})
        login_user(request, user)
        messages.success(request, f"Welcome back, {user.username}.")
        next_url = request.GET.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect("accounts:me")


class LogoutView(View):
    """POST or GET: log out and redirect to login."""

    def get(self, request: HttpRequest) -> HttpResponse:
        logout_user(request)
        messages.info(request, "You have been logged out.")
        return redirect("accounts:login")

    def post(self, request: HttpRequest) -> HttpResponse:
        logout_user(request)
        messages.info(request, "You have been logged out.")
        return redirect("accounts:login")


class RegisterView(View):
    """GET: show registration form. POST: create user and log in (or redirect to login)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        if get_request_user(request):
            return redirect("accounts:me")
        return render(request, "accounts/register.html", {"form": RegisterForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = RegisterForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/register.html", {"form": form}, status=400)
        user = form.save(commit=False)
        user.password = make_password(form.cleaned_data["password"])
        user.is_organizer = form.cleaned_data.get("is_organizer", False)
        user.email = form.cleaned_data["email"]
        user.username = form.cleaned_data["username"]
        user.save()
        login_user(request, user)
        messages.success(request, "Account created. Welcome to Tickr!")
        return redirect("accounts:me")


class MeView(View):
    """GET: current user profile (login required)."""

    @method_decorator(login_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        user = get_request_user(request)
        has_organizer_profile = hasattr(user, "organizer_profile") and user.organizer_profile
        return render(
            request,
            "accounts/me.html",
            {"user": user, "has_organizer_profile": has_organizer_profile},
        )


class OrganizerProfileView(View):
    """GET: show organizer profile (or form). POST: create. PUT-style POST: update."""

    @method_decorator(organizer_required)
    def get(self, request: HttpRequest) -> HttpResponse:
        user = get_request_user(request)
        try:
            profile = user.organizer_profile
            form = OrganizerProfileForm(instance=profile)
        except OrganizerProfile.DoesNotExist:
            profile = None
            form = OrganizerProfileForm()
        return render(
            request,
            "accounts/organizer_profile.html",
            {"form": form, "profile": profile},
        )

    @method_decorator(organizer_required)
    def post(self, request: HttpRequest) -> HttpResponse:
        user = get_request_user(request)
        try:
            profile = user.organizer_profile
            form = OrganizerProfileForm(request.POST, instance=profile)
            is_update = True
        except OrganizerProfile.DoesNotExist:
            profile = None
            form = OrganizerProfileForm(request.POST)
            is_update = False

        if not form.is_valid():
            return render(
                request,
                "accounts/organizer_profile.html",
                {"form": form, "profile": profile},
                status=400,
            )
        form.save(user=user)
        if is_update:
            messages.success(request, "Organizer profile updated.")
        else:
            messages.success(request, "Organizer profile created.")
        return redirect("organizer_profile")
