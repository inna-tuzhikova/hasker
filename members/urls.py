from django.urls import path

from .views import MemberLoginView, MemberLogoutView, MemberSettingsView, signup

urlpatterns = [
    path('login/', MemberLoginView.as_view(), name='login'),
    path('logout/', MemberLogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('settings/', MemberSettingsView.as_view(), name='settings'),
]
