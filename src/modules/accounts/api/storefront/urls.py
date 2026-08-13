from django.urls import path

from modules.accounts.api.storefront.views import (
    LoginView,
    MeView,
    RegisterView,
    VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="accounts-register"),
    path("verify-email", VerifyEmailView.as_view(), name="accounts-verify-email"),
    path("login", LoginView.as_view(), name="accounts-login"),
    path("me", MeView.as_view(), name="accounts-me"),
]
