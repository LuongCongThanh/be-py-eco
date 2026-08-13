"""StaffTOTPDevice — hand-rolled against Staff, not `django_otp.models.Device`
(which FKs to `AUTH_USER_MODEL`; Staff deliberately isn't that — see
staff.py). Uses django-otp's TOTP algorithm/util functions directly
(commit 11's "wire django-otp").
"""

from __future__ import annotations

from binascii import unhexlify

from django.db import models
from django_otp.oath import totp
from django_otp.util import random_hex

from common.db.models import BaseModel
from modules.accounts.models.staff import Staff


def _generate_totp_key() -> str:
    # Named function, not a lambda — Django's migration serializer can't
    # serialize a lambda default (see common/db/models.generate_id for the
    # analogous issue with a shadowed module attribute). No validators
    # either: django_otp.util.hex_validator() returns an unpicklable
    # closure, and this field is only ever set programmatically anyway.
    return random_hex(20)


class StaffTOTPDevice(BaseModel):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="totp_device")
    key = models.CharField(
        max_length=80,
        default=_generate_totp_key,
        help_text="Hex-encoded shared secret.",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_staff_totp_device"

    def __str__(self) -> str:
        return str(self.staff_id)

    @property
    def bin_key(self) -> bytes:
        return unhexlify(self.key)

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None

    def verify_token(self, token: str) -> bool:
        try:
            token_int = int(token)
        except ValueError:
            return False
        return any(totp(self.bin_key, drift=drift) == token_int for drift in (0, -1))
