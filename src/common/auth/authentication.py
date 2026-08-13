"""JWT authentication dispatching by an `actor_type` claim.

Customer and Staff are deliberately not Django's `AUTH_USER_MODEL` (see
modules/accounts/models/customer.py), so simplejwt's default `get_user()`
(a single AUTH_USER_MODEL lookup) doesn't apply — this subclass looks the
actor up in the right table based on the token's `actor_type` claim.
"""

from __future__ import annotations

from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token

ACTOR_TYPE_CLAIM = "actor_type"
CUSTOMER_ACTOR_TYPE = "customer"


class JWTAuthentication(BaseJWTAuthentication):
    # simplejwt's base signature is generic over AbstractBaseUser; Customer/
    # Staff intentionally aren't (see modules/accounts/models/customer.py).
    def get_user(self, validated_token: Token) -> object:  # type: ignore[override]
        actor_type = validated_token.get(ACTOR_TYPE_CLAIM)
        actor_id = validated_token.get(api_settings.USER_ID_CLAIM)

        if actor_type == CUSTOMER_ACTOR_TYPE:
            from modules.accounts.models import Customer

            try:
                return Customer.objects.get(id=actor_id, is_active=True)
            except Customer.DoesNotExist:
                raise InvalidToken("No active customer found for the given token.") from None

        raise InvalidToken("Token is missing a recognized actor_type claim.")
