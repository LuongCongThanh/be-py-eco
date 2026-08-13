from uuid import uuid4

import pytest

from modules.accounts.errors import InvalidRefreshTokenError, SessionNotFoundError
from modules.accounts.models import Session
from modules.accounts.services.register_customer import register_customer
from modules.accounts.services.sessions import (
    issue_session,
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
)


@pytest.mark.django_db
def test_issue_session_creates_a_session_row() -> None:
    result = register_customer(email="session1@example.com", password="a-strong-password-123")

    access, refresh = issue_session(result.customer)

    assert access
    assert refresh
    assert Session.objects.filter(customer=result.customer).count() == 1


@pytest.mark.django_db
def test_rotate_refresh_token_revokes_old_and_issues_new() -> None:
    result = register_customer(email="session2@example.com", password="a-strong-password-123")
    _, old_refresh = issue_session(result.customer)

    new_access, new_refresh = rotate_refresh_token(raw_refresh_token=old_refresh)

    assert new_access
    assert new_refresh != old_refresh
    assert Session.objects.filter(customer=result.customer).count() == 2
    assert Session.objects.filter(customer=result.customer, revoked_at__isnull=False).count() == 1


@pytest.mark.django_db
def test_rotate_refresh_token_rejects_reuse_of_an_already_rotated_token() -> None:
    result = register_customer(email="session3@example.com", password="a-strong-password-123")
    _, old_refresh = issue_session(result.customer)
    rotate_refresh_token(raw_refresh_token=old_refresh)

    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(raw_refresh_token=old_refresh)


@pytest.mark.django_db
def test_rotate_refresh_token_rejects_garbage_token() -> None:
    with pytest.raises(InvalidRefreshTokenError):
        rotate_refresh_token(raw_refresh_token="not-a-real-token")


@pytest.mark.django_db
def test_revoke_session_marks_it_revoked() -> None:
    result = register_customer(email="session4@example.com", password="a-strong-password-123")
    issue_session(result.customer)
    session = Session.objects.get(customer=result.customer)

    revoke_session(customer=result.customer, session_id=session.id)

    session.refresh_from_db()
    assert session.revoked_at is not None


@pytest.mark.django_db
def test_revoke_session_raises_when_not_found() -> None:
    result = register_customer(email="session5@example.com", password="a-strong-password-123")

    with pytest.raises(SessionNotFoundError):
        revoke_session(customer=result.customer, session_id=uuid4())


@pytest.mark.django_db
def test_revoke_all_sessions_revokes_every_active_session() -> None:
    result = register_customer(email="session6@example.com", password="a-strong-password-123")
    issue_session(result.customer)
    issue_session(result.customer)

    revoke_all_sessions(customer=result.customer)

    assert Session.objects.filter(customer=result.customer, revoked_at__isnull=True).count() == 0
