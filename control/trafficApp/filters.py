import django_filters
from django import forms               # ← import Django’s forms
from django.db import models
from .models import Boat

class EntryFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_all',
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search...'})
    )

    class Meta:
        model = Boat
        fields = ['q']
#testtestetst - remove

