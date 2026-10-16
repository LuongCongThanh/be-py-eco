"""Presigned-POST credential factory for direct browser→S3-compatible
uploads — guild.md §15 Slice 2, commit 8.

`django-storages`'s `S3Storage` covers everything else this project needs
from S3 (the `default` `STORAGES` backend, used for reading `ready`
derivatives), but it has no equivalent of `generate_presigned_post` with
key/size/content-type conditions — that's a raw boto3 client concern, so
this thin wrapper exists per Issue #7's Decision Document ("only add a
wrapper if django-storages's default backend can't cleanly express the
requirement").
"""

from __future__ import annotations

import boto3
import environ

env = environ.Env()

QUARANTINE_PREFIX = "quarantine/"
DEFAULT_EXPIRES_IN_SECONDS = 300  # ~5 min, per Issue #7 commit 8's verify criterion


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=env("AWS_S3_ENDPOINT_URL", default="http://localhost:9000"),
        aws_access_key_id=env("AWS_ACCESS_KEY_ID", default="minioadmin"),
        aws_secret_access_key=env("AWS_SECRET_ACCESS_KEY", default="minioadmin"),
    )


def generate_presigned_upload(
    *,
    key: str,
    content_type: str,
    max_size_bytes: int,
    expires_in: int = DEFAULT_EXPIRES_IN_SECONDS,
) -> dict:
    """Return `{"url": ..., "fields": {...}}` for a presigned POST into
    `key` (expected to already be under `QUARANTINE_PREFIX`, with a
    randomly-generated name — never derived from client input)."""
    client = _s3_client()
    bucket = env("AWS_STORAGE_BUCKET_NAME", default="be-py-eco-local")
    return client.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, max_size_bytes],
        ],
        ExpiresIn=expires_in,
    )
