from django.urls import path

from .views import (
    MemberLoginView,
    MemberLogoutView,
    MemberSettingsView,
    MemberSignupView,
)

urlpatterns = [
    path('login/', MemberLoginView.as_view(), name='login'),
    path('logout/', MemberLogoutView.as_view(), name='logout'),
    path('signup/', MemberSignupView.as_view(), name='signup'),
    path('settings/', MemberSettingsView.as_view(), name='settings'),
]
