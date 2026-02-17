from django import forms
from .models import PromoCode


class PromoCodeForm(forms.ModelForm):
    """Create / update a promo code (organizer-facing)."""

    class Meta:
        model = PromoCode
        fields = ("code", "discount_type", "discount_value", "usage_limit", "expires_at", "is_active")
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. SAVE20"}),
            "discount_type": forms.Select(attrs={"class": "form-input"}),
            "discount_value": forms.NumberInput(attrs={"class": "form-input", "min": "0", "step": "0.01"}),
            "usage_limit": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }


class PromoCodeValidateForm(forms.Form):
    """Validate a promo code against an event (user-facing)."""
    code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter promo code"}),
    )
    event_id = forms.UUIDField(widget=forms.HiddenInput())
