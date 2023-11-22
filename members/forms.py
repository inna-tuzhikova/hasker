from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Member


class SignUpForm(UserCreationForm):
    avatar = forms.CharField(max_length=2)
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'avatar')


class MemberUpdateForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['avatar']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
