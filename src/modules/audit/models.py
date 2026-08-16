"""Immutable audit log — write-only in this slice (Issue #6 commit 14); the
query/report API, 2-year retention enforcement, and the centralized
redaction pipeline reused across API/worker/webhook/Sentry are Slice 7's
job (guild.md "Out of Scope"). No update/delete API is exposed here at all
(guild.md §12.3 "Bất biến và không có update/delete API").
"""

from __future__ import annotations

from django.db import models

from common.db.models import BaseModel


class AuditLogEntry(BaseModel):
    actor_type = models.CharField(max_length=20)  # "staff" | "customer"
    actor_id = models.CharField(max_length=64, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=64, blank=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "audit_log_entry"

    def __str__(self) -> str:
        return f"{self.action}:{self.resource_type}:{self.resource_id}"
