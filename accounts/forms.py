from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    SetPasswordForm,
)
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe


class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join(
            f'<div class="alert alert-danger" role="alert">{e}</div>'
            for e in self
        ))


class CustomUserCreationForm(UserCreationForm):
    """
    Registration form (unchanged except for an extra birth-city field).
    """
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    birth_city = forms.CharField(
        required=True,
        label='Birth city (security answer)',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "birth_city",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].help_text = None
            css = self.fields[fieldname].widget.attrs.get('class', '')
            self.fields[fieldname].widget.attrs['class'] = (
                css + ' form-control'
            ).strip()


class SecurityQuestionForm(forms.Form):
    """
    Step 1 of reset: username + answer.
    """
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    birth_city = forms.CharField(
        label='In what city were you born?',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )


class NewPasswordForm(SetPasswordForm):
    """
    Step 2: choose a new password (uses Django’s validation).
    """
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
