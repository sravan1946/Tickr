from django import forms


class CheckInForm(forms.Form):
    """Simple form to accept a ticket code for check-in."""

    code = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter ticket code",
                "autofocus": True,
            }
        ),
    )
