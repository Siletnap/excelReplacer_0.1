from django import forms
from django.forms.widgets import DateInput
import datetime

from .models import Boat

class NewBoatForm(forms.ModelForm):
    # 1) Single declaration of booking_type with hardcoded tuples
    BOOKING_CHOICES = [
        ('yearly',        'Yearly'),
        ('daily_monthly', 'Daily / Monthly'),
        ('guest',         'Guest'),
    ]
    booking_type = forms.ChoiceField(
        choices=BOOKING_CHOICES,
        widget=forms.RadioSelect,
        label="Booking Type"
    )  # :contentReference[oaicite:0]{index=0}

    # 2) Date fields use proper DateField for validation, with HTML5 picker
    cid  = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'}),
        label="Check‑In Date"
    )   # :contentReference[oaicite:1]{index=1}
    ecod = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'}),
        label="Check‑Out Date"
    )   # :contentReference[oaicite:2]{index=2}

    class Meta:
        model  = Boat
        fields = [
            'boatType', 'name', 'berth', 'state',
            'booking_type', 'cid', 'ecod'
        ]
        # No need for Meta.widgets since fields declare their own widgets

    def clean(self):
        cleaned = super().clean()
        btype = cleaned.get('booking_type')
        cid = cleaned.get('cid')
        ecod = cleaned.get('ecod')

        if btype == 'yearly':
            cleaned['cid'] = 'Yearly'
            cleaned['ecod'] = 'Yearly'
        elif btype == 'guest':
            cleaned['cid'] = 'Guest'
            cleaned['ecod'] = 'Guest'
        else:
            if cid is None:
                raise forms.ValidationError("Please select a check‑in date.")
            if ecod is None:
                # 1) Mutate both cleaned_data and instance
                cleaned['cid'] = cid.strftime('%Y/%m/%d')
                cleaned['ecod'] = "Unknown"
                self.instance.cid = cleaned['cid']
                self.instance.ecod = cleaned['ecod']
            else:
                if cid >= ecod:
                    raise forms.ValidationError(
                        "Check‑out date must be later than check‑in date."
                    )

                cleaned['cid'] = cid.strftime('%Y/%m/%d')
                cleaned['ecod'] = ecod.strftime('%Y/%m/%d')
                self.instance.cid = cleaned['cid']
                self.instance.ecod = cleaned['ecod']

        return cleaned


