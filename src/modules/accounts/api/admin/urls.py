from django.urls import path

from modules.accounts.api.admin.views import (
    CreateStaffView,
    DisableCustomerView,
    MfaConfirmView,
    MfaSetupView,
    ResetStaffMfaView,
    StaffLoginView,
)

urlpatterns = [
    path("staff/login", StaffLoginView.as_view(), name="admin-staff-login"),
    path("staff", CreateStaffView.as_view(), name="admin-staff-create"),
    path("staff/mfa/setup", MfaSetupView.as_view(), name="admin-staff-mfa-setup"),
    path("staff/mfa/confirm", MfaConfirmView.as_view(), name="admin-staff-mfa-confirm"),
    path(
        "staff/<uuid:staff_id>/mfa/reset",
        ResetStaffMfaView.as_view(),
        name="admin-staff-mfa-reset",
    ),
    path(
        "customers/<uuid:customer_id>/disable",
        DisableCustomerView.as_view(),
        name="admin-customer-disable",
    ),
]
