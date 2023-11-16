from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import SignUpForm


class MemberLoginView(LoginView):
    redirect_authenticated_user = True
    next_page = 'questions:index'

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password')
        return self.render_to_response(self.get_context_data(form=form))


class MemberLogoutView(LogoutView):
    next_page = 'questions:index'


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.profile.avatar = form.cleaned_data.get('avatar')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('questions:index')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', dict(form=form))

