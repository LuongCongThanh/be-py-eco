from django.urls import path

from modules.accounts.api.storefront.views import (
    LoginView,
    MeView,
    RefreshTokenView,
    RegisterView,
    SessionListView,
    SessionRevokeAllView,
    SessionRevokeView,
    VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="accounts-register"),
    path("verify-email", VerifyEmailView.as_view(), name="accounts-verify-email"),
    path("login", LoginView.as_view(), name="accounts-login"),
    path("token/refresh", RefreshTokenView.as_view(), name="accounts-token-refresh"),
    path("me", MeView.as_view(), name="accounts-me"),
    path("sessions", SessionListView.as_view(), name="accounts-sessions"),
    path(
        "sessions/<uuid:session_id>/revoke",
        SessionRevokeView.as_view(),
        name="accounts-session-revoke",
    ),
    path(
        "sessions/revoke-all", SessionRevokeAllView.as_view(), name="accounts-sessions-revoke-all"
    ),
]
