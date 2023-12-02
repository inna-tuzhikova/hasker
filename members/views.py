from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.forms import Form
from django.shortcuts import redirect, render
from django.views.generic.base import ContextMixin, View

from questions.views import TopTrendingQuestionsMixin

from .forms import MemberUpdateForm, SignUpForm, UserUpdateForm


class MemberLoginView(TopTrendingQuestionsMixin, LoginView):
    """Allows user to login"""
    redirect_authenticated_user = True
    next_page = 'questions:index'

    def form_invalid(self, form: Form):
        messages.error(self.request, 'Invalid username or password!')
        return self.render_to_response(self.get_context_data(form=form))


class MemberLogoutView(LogoutView):
    """Allows user to logout"""
    next_page = 'questions:index'


def signup(request):
    """New user registration"""
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
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
    trending = TopTrendingQuestionsMixin.get_trending()
    return render(
        request,
        'registration/signup.html',
        {
            'form': form,
            TopTrendingQuestionsMixin.trending_ctx_name: trending
        }
    )


class MemberSettingsView(
    TopTrendingQuestionsMixin,
    LoginRequiredMixin,
    ContextMixin,
    View
):
    """Allows user to check and edit settings"""
    login_url = 'login'
    template_name = 'members/settings.html'

    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        member_form = MemberUpdateForm(instance=request.user.profile)
        context = self.get_context_data(
            form=user_form,
            member_form=member_form
        )
        return render(request, self.template_name, context=context)

    def post(self, request):
        user_form = UserUpdateForm(request.POST)
        member_form = MemberUpdateForm(request.POST, request.FILES)
        if user_form.is_valid() and member_form.is_valid():
            request.user.email = user_form.cleaned_data['email']
            request.user.save()
            request.user.profile.avatar = member_form.cleaned_data['avatar']
            request.user.profile.save()
            return redirect('settings')
        context = self.get_context_data(
            form=user_form,
            member_form=member_form
        )
        return render(request, self.template_name, context)
