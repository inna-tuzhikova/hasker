from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Member


class SignUpForm(UserCreationForm):
    """Form with data for user registration"""
    avatar = forms.ImageField(required=False)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'avatar')


class MemberUpdateForm(forms.ModelForm):
    """Form with data for user settings check/editing"""
    class Meta:
        model = Member
        fields = ['avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].required = False


class UserUpdateForm(forms.ModelForm):
    """Form with data for user settings check/editing"""
    class Meta:
        model = User
        fields = ['email']
