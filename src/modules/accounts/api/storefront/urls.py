from django.urls import path

from modules.accounts.api.storefront.views import (
    ConfirmEmailChangeView,
    ConfirmPasswordResetView,
    GoogleLoginView,
    LoginView,
    MeView,
    RefreshTokenView,
    RegisterView,
    RequestEmailChangeView,
    RequestPasswordResetView,
    SessionListView,
    SessionRevokeAllView,
    SessionRevokeView,
    UpdateLocalePreferenceView,
    VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="accounts-register"),
    path("verify-email", VerifyEmailView.as_view(), name="accounts-verify-email"),
    path("login", LoginView.as_view(), name="accounts-login"),
    path("login/google", GoogleLoginView.as_view(), name="accounts-login-google"),
    path("token/refresh", RefreshTokenView.as_view(), name="accounts-token-refresh"),
    path("me", MeView.as_view(), name="accounts-me"),
    path("me/locale", UpdateLocalePreferenceView.as_view(), name="accounts-me-locale"),
    path("sessions", SessionListView.as_view(), name="accounts-sessions"),
    path(
        "sessions/<uuid:session_id>/revoke",
        SessionRevokeView.as_view(),
        name="accounts-session-revoke",
    ),
    path(
        "sessions/revoke-all", SessionRevokeAllView.as_view(), name="accounts-sessions-revoke-all"
    ),
    path(
        "password-reset/request",
        RequestPasswordResetView.as_view(),
        name="accounts-password-reset-request",
    ),
    path(
        "password-reset/confirm",
        ConfirmPasswordResetView.as_view(),
        name="accounts-password-reset-confirm",
    ),
    path(
        "email-change/request",
        RequestEmailChangeView.as_view(),
        name="accounts-email-change-request",
    ),
    path(
        "email-change/confirm",
        ConfirmEmailChangeView.as_view(),
        name="accounts-email-change-confirm",
    ),
]
