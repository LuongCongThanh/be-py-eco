"""Permission framework: codename-based checks against a role, plus an
object-level policy helper. Called from application services — never from
views (guild.md §2.5: "Không rải if user.role == ... trong view").

`ROLE_PERMISSIONS` is the single source of truth mapping each business role
to the codenames it holds; each module adds its own sensitive-action
codenames here as they're defined (the first is accounts.create_staff,
added when Staff accounts land).
"""

from __future__ import annotations

from collections.abc import Callable

MASTER_ADMIN = "master_admin"
STORE_MANAGER = "store_manager"
ORDER_STAFF = "order_staff"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    MASTER_ADMIN: {
        "accounts.create_staff",
        "accounts.disable_customer",
        "accounts.reset_staff_mfa",
    },
    STORE_MANAGER: {"accounts.disable_customer"},
    ORDER_STAFF: set(),
}

ObjectPolicyCheck = Callable[[object], bool]


class PermissionDeniedError(Exception):
    """Raised by services (not views) when a policy check fails."""


def has_permission(role: str, codename: str) -> bool:
    return codename in ROLE_PERMISSIONS.get(role, set())


def check_policy(
    *,
    role: str,
    codename: str,
    obj: object = None,
    object_check: ObjectPolicyCheck | None = None,
) -> bool:
    """`role` must hold `codename`; if `object_check` is given, it must also
    pass against `obj` (object-level policy, e.g. "only the assigned Order
    Staff may act on this specific Order")."""
    if not has_permission(role, codename):
        return False
    return object_check(obj) if object_check is not None else True


def require_permission(
    *,
    role: str,
    codename: str,
    obj: object = None,
    object_check: ObjectPolicyCheck | None = None,
) -> None:
    if not check_policy(role=role, codename=codename, obj=obj, object_check=object_check):
        raise PermissionDeniedError(f"Role '{role}' lacks permission '{codename}'.")
