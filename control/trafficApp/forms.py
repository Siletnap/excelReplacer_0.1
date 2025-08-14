from django import forms
from django.forms.widgets import DateInput, TimeInput
import datetime
from .models import Boat, TrafficEntry

class NewTrafficForm(forms.ModelForm):
    trDate = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'}),
        label="Date"
    )
    trTime = forms.TimeField(
        required=False,
        widget=TimeInput(attrs={'type': 'time', 'step': '60'}),
        label="Time",
    )
    edr = forms.DateField(
        required=False,
        widget=DateInput(attrs={'type': 'date'}),
        label="Date"
    )
    etr = forms.TimeField(
        required=False,
        widget=TimeInput(attrs={'type': 'time', 'step': '60'}),
        label="Time",
    )

    def save(self, commit=True):
        obj = super().save(commit=False)
        trDate = self.cleaned_data.get('trDate')
        edr    = self.cleaned_data.get('edr')
        obj.trDate = trDate.strftime('%Y/%m/%d') if trDate else ''
        obj.edr    = edr.strftime('%Y/%m/%d') if edr else ''
        if commit:
            obj.save()
        return obj

    class Meta:
        model  = TrafficEntry
        fields = [
            'boatType', 'name', 'trDate', 'trTime',
            'direction', 'passengers', 'purpose',
            'edr', 'etr', 'trComments', 'berth'
        ]

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


