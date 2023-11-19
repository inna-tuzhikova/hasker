from django.urls import path
from django.contrib.auth import views as auth_views

from .views import MemberLoginView, MemberLogoutView, signup


urlpatterns = [
    path('login/', MemberLoginView.as_view(), name='login'),
    path('logout/', MemberLogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    # path('settings/', MemberSignUpView.as_view(), name='settings'),
]