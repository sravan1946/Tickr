from django import forms
from .models import Attendee


class OrderTicketForm(forms.Form):
    """Dynamic form for selecting ticket quantities — rendered per TicketType."""
    ticket_type_id = forms.UUIDField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(
            attrs={"class": "form-input", "min": "0", "style": "width: 5rem;"},
        ),
    )


class AttendeeForm(forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ("full_name", "email")
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Full name"},
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "Email address"},
            ),
        }
