from django.urls import path

from modules.accounts.api.storefront.views import RegisterView, VerifyEmailView

urlpatterns = [
    path("register", RegisterView.as_view(), name="accounts-register"),
    path("verify-email", VerifyEmailView.as_view(), name="accounts-verify-email"),
]
