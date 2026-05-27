from django.urls import path

from .views import LoginView, LogoutView, MeView, SignupView

urlpatterns = [
    path("auth/signup", SignupView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("me", MeView.as_view()),
]
