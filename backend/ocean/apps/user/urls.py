from django.urls import path

from ocean.apps.user.views import LoginView, LogOutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogOutView.as_view(), name="logout"),
]
