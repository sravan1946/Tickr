from django import forms
from django.core.exceptions import ValidationError

from .models import TicketType


class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = (
            "name",
            "price",
            "quantity_total",
            "sale_start",
            "sale_end",
            "is_active",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "e.g., General Admission, VIP",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                }
            ),
            "quantity_total": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "min": "1",
                    "placeholder": "Total tickets",
                }
            ),
            "sale_start": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"}
            ),
            "sale_end": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

    def clean(self) -> dict[str, object]:
        data = super().clean()
        sale_start = data.get("sale_start")
        sale_end = data.get("sale_end")
        if sale_start and sale_end and sale_end <= sale_start:
            raise ValidationError({"sale_end": "Sale end date must be after sale start date."})
        return data
