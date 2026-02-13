from django import forms
from django.core.exceptions import ValidationError

from .models import User, OrganizerProfile


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "you@example.com", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Password"})
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Password"}),
        min_length=8,
        help_text="At least 8 characters.",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Confirm password"}),
        label="Confirm password",
    )
    is_organizer = forms.BooleanField(
        required=False,
        initial=False,
        label="I'm an organizer",
    )

    class Meta:
        model = User
        fields = ("email", "username")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "you@example.com"}),
            "username": forms.TextInput(attrs={"class": "form-input", "placeholder": "Username"}),
        }

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self) -> str:
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean(self) -> dict[str, object]:
        data = super().clean()
        if data.get("password") != data.get("password_confirm"):
            raise ValidationError({"password_confirm": "Passwords do not match."})
        return data


class OrganizerProfileForm(forms.ModelForm):
    class Meta:
        model = OrganizerProfile
        fields = ("organization_name", "contact_email", "contact_phone")
        widgets = {
            "organization_name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Your organization name"}
            ),
            "contact_email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "contact@org.com"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "+1 234 567 8900"}
            ),
        }

    def save(
        self,
        commit: bool = True,
        user: User | None = None,
    ) -> OrganizerProfile:
        instance = super().save(commit=False)
        if user is not None and instance.pk is None:
            instance.user = user
        if commit:
            instance.save()
        return instance
