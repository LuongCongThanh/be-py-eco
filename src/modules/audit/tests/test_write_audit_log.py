import pytest

from modules.audit.models import AuditLogEntry
from modules.audit.services.write_audit_log import _redact, write_audit_log


@pytest.mark.django_db
def test_write_audit_log_persists_actor_action_resource() -> None:
    entry = write_audit_log(
        actor_type="staff",
        actor_id="staff-1",
        action="accounts.create_staff",
        resource_type="staff",
        resource_id="staff-2",
        before={},
        after={"email": "x@example.com"},
    )

    stored = AuditLogEntry.objects.get(id=entry.id)
    assert stored.actor_type == "staff"
    assert stored.action == "accounts.create_staff"
    assert stored.after == {"email": "x@example.com"}


@pytest.mark.django_db
def test_write_audit_log_redacts_secret_shaped_keys() -> None:
    entry = write_audit_log(
        actor_type="staff",
        actor_id="staff-1",
        action="accounts.create_staff",
        resource_type="staff",
        resource_id="staff-2",
        before={"password": "super-secret", "email": "x@example.com"},
        after={"password_hash": "argon2$...", "token": "abc123"},
    )

    assert entry.before == {"password": "<redacted>", "email": "x@example.com"}
    assert entry.after == {"password_hash": "<redacted>", "token": "<redacted>"}


def test_redact_treats_none_and_empty_as_empty_dict() -> None:
    assert _redact(None) == {}
    assert _redact({}) == {}
