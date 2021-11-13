from django import forms
import datetime

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import *


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class NumberInput(forms.NumberInput):
    input_type = 'number'


class CreateOutingForm(ModelForm):
    class Meta:
        model = Outing
        fields = ['date', 'meetingTime', 'boat', 'team']
        widgets = {
            'date': DateInput(),
            'meetingTime': TimeInput(),
        }


class SignupOutingForm(ModelForm):
    class Meta:
        model = Available
        fields = ['outing', 'type']


class BookErgForm(ModelForm):
    class Meta:
        model = ErgBooking
        fields = ['startTime', 'hours', 'erg', 'date']
        widgets = {
            'startTime': TimeInput(),
            'hours': NumberInput(attrs={'min': '0', 'max': '8', 'step': 1}),
            'date': forms.HiddenInput(),
            'erg': forms.HiddenInput()
        }

class CreateErgWorkout(ModelForm):
    class Meta:
        model = ErgWorkout
        fields = ['date', 'distance', 'minutes', 'seconds', 'subSeconds']
        widgets = {
            'date': DateInput(),
            'distance': NumberInput(attrs={'min': '0', 'max': '99999', 'step': 1}),
            'minutes': NumberInput(attrs={'min': '0', 'max': '999', 'step': 1}),
            'seconds': NumberInput(attrs={'min': '0', 'max': '59', 'step': 1}),
            'subSeconds': NumberInput(attrs={'min': '0', 'max': '9', 'step': 1}),
        }


class SignupUsersBulkForm(forms.Form):
    val = forms.TextInput()


class DeleteWorkoutForm(forms.Form):
    w_id = forms.NumberInput()
