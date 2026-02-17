from django import forms
from django.core.exceptions import ValidationError

from .models import Event, EventCategory, Venue


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = (
            "title",
            "slug",
            "description",
            "category",
            "venue",
            "start_date",
            "end_date",
            "capacity",
            "is_published",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Event title"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "url-friendly-name"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-input", "rows": 4, "placeholder": "Describe your event"}
            ),
            "category": forms.Select(attrs={"class": "form-input"}),
            "venue": forms.Select(attrs={"class": "form-input"}),
            "start_date": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "form-input", "type": "datetime-local"}
            ),
            "capacity": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "placeholder": "Event capacity"}
            ),
            "is_published": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

    def clean(self) -> dict[str, object]:
        data = super().clean()
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and end <= start:
            raise ValidationError({"end_date": "End date must be after start date."})
        return data
