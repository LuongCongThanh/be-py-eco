"""Unit tests: permission-policy helper (allow/deny independent of any
view or HTTP request) — guild.md §10.2 unit test requirement for commit 10.
"""

import pytest

from common.auth import permissions
from common.auth.permissions import (
    ORDER_STAFF,
    PermissionDeniedError,
    check_policy,
    has_permission,
    require_permission,
)


def test_has_permission_true_when_role_holds_codename(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(permissions.ROLE_PERMISSIONS, "example_role", {"example.codename"})

    assert has_permission("example_role", "example.codename") is True


def test_has_permission_false_when_role_lacks_codename() -> None:
    assert has_permission(ORDER_STAFF, "nonexistent.codename") is False


def test_has_permission_false_for_unknown_role() -> None:
    assert has_permission("not_a_real_role", "anything") is False


def test_check_policy_denies_without_the_codename() -> None:
    assert check_policy(role=ORDER_STAFF, codename="nonexistent.codename") is False


def test_check_policy_runs_object_check_only_when_codename_held(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(permissions.ROLE_PERMISSIONS, "example_role_2", {"example.codename"})

    assert (
        check_policy(
            role="example_role_2",
            codename="example.codename",
            obj="matching",
            object_check=lambda obj: obj == "matching",
        )
        is True
    )
    assert (
        check_policy(
            role="example_role_2",
            codename="example.codename",
            obj="other",
            object_check=lambda obj: obj == "matching",
        )
        is False
    )


def test_require_permission_raises_when_denied() -> None:
    with pytest.raises(PermissionDeniedError):
        require_permission(role=ORDER_STAFF, codename="nonexistent.codename")


def test_require_permission_passes_silently_when_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(permissions.ROLE_PERMISSIONS, "example_role_3", {"example.codename"})

    require_permission(role="example_role_3", codename="example.codename")
