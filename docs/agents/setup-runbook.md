# Setup Runbook — Slice 0 (Issue #5)

Manual, step-by-step execution guide for standing up the repository skeleton
described in [Issue #5](https://github.com/LuongCongThanh/be-py-eco/issues/5).
Each step below maps 1:1 to a commit in that issue's plan, in the same order.
Every command is copy-pasteable **PowerShell** on Windows — folder creation,
file creation (with full file content), the exact command to run, and the
exact command to activate/verify each tool.

Note: unlike Issue #5's original layout (which nests everything under a
`backend/` subfolder), this runbook installs the Django project **directly at
the repo root** — `./pyproject.toml`, `./src/config/...`, `./manage.py`,
`./tests/...`, no `backend/` prefix anywhere. `guild.md` §7.2 has been updated
to match.

Note: on this machine, a Windows Application Control (WDAC/AppLocker-style)
policy blocks spawning `pytest.exe`/`mypy.exe`/`celery.exe` directly — use
`uv run python -m pytest` (works) instead of `uv run pytest`. `mypy` is
blocked even via `python -m mypy` (its compiled extension DLL is blocked
too); if that's also the case for you, treat `mypy` as CI-only until IT
allowlists it locally.

How to use this document:

- Work through the steps in order — each one assumes the previous steps are done.
- Run the commands, confirm the check passes, then commit before moving on.
- All commands are run from the repo root unless a step says otherwise.
- File-creation commands use PowerShell here-strings
  (`@'...'@ | Set-Content -Path <file> -Encoding utf8`). The closing `'@`
  must be at column 0 (no leading whitespace) — that's a PowerShell syntax
  requirement, not a typo.

---

## Step 0 — Upgrade to Python 3.13

`pyproject.toml` (added in Step 1) pins `>=3.13,<3.14`. If the machine's
default Python is older, install 3.13 via `uv` first.

```powershell
uv python install 3.13
uv python list
```

**Check**: `3.13.x` appears in the `uv python list` output, marked as installed.

```powershell
git add -A
git commit -m "chore: pin uv-managed Python 3.13 toolchain"
```

---

## Step 1 — Add the full pinned dependency manifest

```powershell
uv init --python 3.13 --no-workspace .
Remove-Item main.py -ErrorAction SilentlyContinue   # uv init's placeholder script — not needed

# Core API
uv add django==5.2.17 djangorestframework==3.18.0 "psycopg[binary]==3.3.4" django-environ==0.14.0 django-filter==26.1 drf-spectacular==0.30.0 drf-standardized-errors==0.16.0 django-cors-headers==4.9.0

# Auth / security
uv add djangorestframework-simplejwt==5.5.1 django-allauth==65.19.0 django-otp==1.7.0 django-axes==8.3.1 argon2-cffi==25.1.0 cryptography==50.0.0 django-countries==9.0.0 phonenumberslite==9.0.36

# Background / provider
uv add celery==5.6.3 django-celery-beat==2.9.0 redis==8.1.0 opensearch-py==3.2.0 httpx==0.28.1 tenacity==9.1.4

# Media
uv add django-storages==1.14.6 boto3==1.43.69 Pillow==12.3.0 filetype==1.2.0

# Observability
uv add structlog==26.1.0 sentry-sdk==2.67.1 prometheus-client==0.26.0

# Testing (dev group)
uv add --group dev pytest==9.1.1 pytest-django==4.14.0 pytest-cov==7.1.0 factory-boy==3.3.3 hypothesis==6.165.3 freezegun==1.5.5 respx==0.23.1

# Dev / supply-chain (dev group)
uv add --group dev ruff==0.16.2 mypy==2.3.0 django-stubs==6.0.9 "celery-types>=0.26.0" pip-audit==2.10.1 bandit==1.9.4 detect-secrets==1.5.0
```

> Windows note: plain `psycopg==3.3.4` fails to import with
> `no pq wrapper available` because there's no system `libpq` on Windows by
> default. The `[binary]` extra above bundles a prebuilt libpq — do not
> install plain `psycopg` on Windows.

Create `.gitignore` (repo root):

```powershell
@'
.venv/
__pycache__/
*.pyc
.env
.idea/
'@ | Set-Content -Path .gitignore -Encoding utf8
```

**Check**: `uv sync` completes with no resolution errors.

```powershell
uv sync
git add -A
git commit -m "chore: add pinned dependency manifest"
```

---

## Step 2 — Add the local Docker Compose environment (PostgreSQL only)

```powershell
New-Item -ItemType Directory -Force -Path infra/compose | Out-Null
```

```powershell
@'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-be_py_eco}
      POSTGRES_USER: ${POSTGRES_USER:-be_py_eco}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-be_py_eco}
    ports:
      # Host port 5433, not 5432 — if this machine already has a native
      # PostgreSQL Windows service bound to 5432 (`Get-Service *postgres*`),
      # the Compose container would silently lose that port to it and
      # Django would connect to the wrong server. Remap instead of touching
      # the native service.
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-be_py_eco}"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  postgres_data:
'@ | Set-Content -Path infra/compose/docker-compose.yml -Encoding utf8
```

```powershell
@'
# Copy this file to .env and adjust values for local development.
# Never commit a real .env — it may contain secrets.

DEBUG=True
SECRET_KEY=change-me-in-local-env

# Points Django at the Compose postgres service (infra/compose/docker-compose.yml).
DATABASE_URL=psql://be_py_eco:be_py_eco@localhost:5433/be_py_eco
POSTGRES_DB=be_py_eco
POSTGRES_USER=be_py_eco
POSTGRES_PASSWORD=be_py_eco
'@ | Set-Content -Path .env.example -Encoding utf8

Copy-Item .env.example .env
```

```powershell
docker compose -f infra/compose/docker-compose.yml up -d postgres
docker compose -f infra/compose/docker-compose.yml ps
docker exec -it <postgres-container-name> pg_isready
```

**Check**: container status is `running`/`healthy`, and `pg_isready` reports
`accepting connections`.

```powershell
git add -A
git commit -m "chore: add local Postgres via docker compose"
```

---

## Step 3 — Bootstrap the Django project

```powershell
New-Item -ItemType Directory -Force -Path src/config/settings | Out-Null
New-Item -ItemType File -Force -Path src/config/__init__.py | Out-Null
New-Item -ItemType File -Force -Path src/config/settings/__init__.py | Out-Null
```

```powershell
@'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"


def main():
    """Run administrative tasks."""
    sys.path.insert(0, str(SRC_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'@ | Set-Content -Path manage.py -Encoding utf8
```

```powershell
@'
"""URL configuration for the be-py-eco project.

Empty for now — the `/api/v1/...` namespace and `/health/*` endpoints land
in Slice 1 (see Issue #5's "Explicit non-decisions" section).
"""

urlpatterns = []
'@ | Set-Content -Path src/config/urls.py -Encoding utf8
```

```powershell
@'
"""WSGI config for the be-py-eco project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
'@ | Set-Content -Path src/config/wsgi.py -Encoding utf8
```

```powershell
@'
"""ASGI config for the be-py-eco project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
'@ | Set-Content -Path src/config/asgi.py -Encoding utf8
```

```powershell
@'
"""Base Django settings — shared, env-driven, no environment-specific defaults.

Every value is read from the environment via django-environ; nothing here
hard-codes a value that would work "by accident" in production.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
'@ | Set-Content -Path src/config/settings/base.py -Encoding utf8
```

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.base"
uv run python manage.py check
```

**Check**: on recent Django versions this may pass cleanly even without
`DATABASES` set (the check command doesn't touch the DB unless asked to) —
either a clean pass or a "no DATABASES configured" failure both prove
settings/env wiring already works. Treat either outcome as success for this step.

```powershell
git add -A
git commit -m "chore: bootstrap Django project skeleton"
```

---

## Step 4 — Wire the database connection

Add `DATABASES` to `base.py`:

```powershell
Add-Content -Path src/config/settings/base.py -Value @'

DATABASES = {
    "default": env.db_url("DATABASE_URL"),
}
'@
```

```powershell
@'
"""Local development settings — Compose Postgres, DEBUG on."""

from .base import *  # noqa: F403

DEBUG = True
'@ | Set-Content -Path src/config/settings/local.py -Encoding utf8
```

```powershell
@'
"""Test settings — real PostgreSQL, never SQLite (guild.md §10.5).

Django's test runner creates a dedicated `test_<NAME>` database from the
`default` connection below, so no separate connection is configured here.
"""

from .base import *  # noqa: F403

DEBUG = False
'@ | Set-Content -Path src/config/settings/test.py -Encoding utf8
```

```powershell
@'
"""Production settings — managed services, strict host checks, no accidental defaults."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

# Connection pooling via psycopg3's built-in pool. Exact pool sizing is an
# infrastructure-sizing decision deferred per Issue #4's Further Notes
# (guild.md §16) — this only turns pooling on, not its size.
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    **DATABASES["default"].get("OPTIONS", {}),  # noqa: F405
    "pool": True,
}
'@ | Set-Content -Path src/config/settings/production.py -Encoding utf8
```

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py check --database default
```

**Check**: no errors — Django connects to the Compose Postgres container.

```powershell
git add -A
git commit -m "chore: wire database connection and settings split"
```

---

## Step 5 — Run the first migration

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py migrate
docker exec -it <postgres-container-name> psql -U be_py_eco -d be_py_eco -c "\dt"
```

**Check**: migration reports success; `\dt` lists Django's built-in tables
(`auth_user`, `django_session`, etc.). This step touches only the database —
no repo files change, so there's nothing new to commit.

---

## Step 6 — Wire pytest against a real PostgreSQL test database

```powershell
Add-Content -Path pyproject.toml -Value @'

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
pythonpath = ["src"]
'@
```

```powershell
New-Item -ItemType Directory -Force -Path tests | Out-Null
New-Item -ItemType File -Force -Path tests/__init__.py | Out-Null
```

```powershell
@'
"""Smoke test proving Django can reach the real PostgreSQL test database.

Per guild.md §10.5: real PostgreSQL only, never SQLite.
"""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_connection_is_reachable():
    connection.ensure_connection()
    assert connection.is_usable()
'@ | Set-Content -Path tests/test_environment.py -Encoding utf8
```

```powershell
uv run python -m pytest
```

**Check**: test suite passes, and `pytest-django` created/used a real
PostgreSQL test database (never SQLite).

```powershell
git add -A
git commit -m "chore: wire pytest against real Postgres test db"
```

---

## Step 7 — Add lint/format tooling

```powershell
Add-Content -Path pyproject.toml -Value @'

[tool.ruff]
line-length = 100
target-version = "py313"
extend-exclude = [".agents", ".claude"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "DJ"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["config", "common", "modules", "integrations"]
'@
```

`extend-exclude` skips `.agents`/`.claude` — this repo vendors agent-skill
docs under those dirs, and some of their example assets are
intentionally-incomplete Python templates that ruff can't parse.

```powershell
uv run ruff format src tests manage.py
uv run ruff check src tests manage.py
uv run ruff format --check src tests manage.py
```

**Check**: both commands exit clean (no errors, no diffs pending).

```powershell
git add -A
git commit -m "chore: add ruff lint/format configuration"
```

---

## Step 8 — Add static type checking

```powershell
Add-Content -Path pyproject.toml -Value @'

[tool.mypy]
mypy_path = "src"
plugins = ["mypy_django_plugin.main"]
python_version = "3.13"
ignore_missing_imports = true
check_untyped_defs = true

[tool.django-stubs]
django_settings_module = "config.settings.test"
'@
```

```powershell
uv run python -m mypy src
```

**Check**: exits clean, no type errors on the current skeleton. If `mypy` is
blocked locally by an Application Control policy (see the top-of-file note),
this becomes CI-only for now — the config is still committed.

```powershell
git add -A
git commit -m "chore: add mypy static type checking"
```

---

## Step 9 — Add the `common/` package skeleton

```powershell
New-Item -ItemType Directory -Force -Path src/common/api, src/common/auth, src/common/db, src/common/money, src/common/ids, src/common/observability, src/common/testing | Out-Null
New-Item -ItemType Directory -Force -Path src/modules, src/integrations | Out-Null
New-Item -ItemType Directory -Force -Path tests/common | Out-Null

New-Item -ItemType File -Force -Path src/common/__init__.py, src/common/api/__init__.py, src/common/auth/__init__.py, src/common/db/__init__.py, src/common/money/__init__.py, src/common/observability/__init__.py, src/common/testing/__init__.py | Out-Null
New-Item -ItemType File -Force -Path src/modules/__init__.py, src/integrations/__init__.py | Out-Null
New-Item -ItemType File -Force -Path tests/common/__init__.py | Out-Null
```

```powershell
@'
"""UUIDv7 generator — time-ordered UUIDs (RFC 9562) for use as primary keys.

Monotonic within the same millisecond via a random tie-breaker in the
remaining bits, so IDs generated in quick succession still sort correctly.
"""

import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a UUIDv7: 48-bit millisecond timestamp + random bits."""
    unix_ms = time.time_ns() // 1_000_000
    timestamp_bytes = unix_ms.to_bytes(6, byteorder="big")
    rand_bytes = bytearray(os.urandom(10))

    # Set version (7) in the high nibble of byte 6.
    rand_bytes[0] = (rand_bytes[0] & 0x0F) | 0x70
    # Set variant (RFC 4122) in the high bits of byte 8.
    rand_bytes[2] = (rand_bytes[2] & 0x3F) | 0x80

    return uuid.UUID(bytes=timestamp_bytes + bytes(rand_bytes))
'@ | Set-Content -Path src/common/ids/uuid7.py -Encoding utf8

@'
from common.ids.uuid7 import uuid7

__all__ = ["uuid7"]
'@ | Set-Content -Path src/common/ids/__init__.py -Encoding utf8
```

```powershell
@'
import uuid

from common.ids import uuid7


def test_uuid7_returns_valid_uuid():
    value = uuid7()
    assert isinstance(value, uuid.UUID)
    assert value.version == 7


def test_uuid7_timestamps_are_non_decreasing():
    # The random suffix isn't ordered, so compare the embedded timestamps
    # (the leading 48 bits) rather than the raw UUID bytes.
    timestamps = [uuid7().int >> 80 for _ in range(1000)]
    assert timestamps == sorted(timestamps)


def test_uuid7_values_are_unique():
    values = [uuid7() for _ in range(1000)]
    assert len(set(values)) == len(values)
'@ | Set-Content -Path tests/common/test_ids.py -Encoding utf8
```

Wire `structlog` JSON logging into `LOGGING` in `base.py`:

```powershell
(Get-Content src/config/settings/base.py -Raw) -replace 'import environ', "import environ`nimport structlog" | Set-Content src/config/settings/base.py -Encoding utf8

Add-Content -Path src/config/settings/base.py -Value @'

# Structured JSON logging (common/observability). Real Sentry DSN / Prometheus
# scrape endpoints are out of scope for this slice — only the JSON log
# pipeline is wired up here.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
'@
```

```powershell
uv run python -m pytest
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py check
```

**Check**: pytest passes (including the new `common/ids` tests). To see the
JSON log line directly:

```powershell
uv run python -c "import sys, os, django; sys.path.insert(0, 'src'); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local'); django.setup(); import structlog; structlog.get_logger('smoke').info('smoke_test', proves='json_logging_wired')"
```

Expect one line of JSON output like
`{"proves": "json_logging_wired", "event": "smoke_test", ...}`.

```powershell
git add -A
git commit -m "chore: add common package skeleton with ids and logging"
```

---

## Step 10 — Add Redis to the environment

```powershell
$compose = Get-Content infra/compose/docker-compose.yml -Raw
$compose = $compose -replace '(?m)^services:', @'
services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

'@.TrimEnd() + "`n`n" + "  postgres:" -replace '  postgres:$', ''
```

> The regex juggling above is fragile to reproduce by hand — simplest in
> practice is to open `infra/compose/docker-compose.yml` in an editor and
> add the `redis:` service block above the existing `postgres:` block, and
> add `redis_data:` under the top-level `volumes:` key. Same approach for
> Steps 11–13 below (RabbitMQ, OpenSearch, MinIO).

Add `CACHES` to `base.py`:

```powershell
Add-Content -Path src/config/settings/base.py -Value @'

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    },
}
'@
```

```powershell
Add-Content -Path .env -Value "REDIS_URL=redis://localhost:6379/0"
Add-Content -Path .env.example -Value "REDIS_URL=redis://localhost:6379/0"
```

```powershell
@'
import environ
import redis

env = environ.Env()


def test_redis_connection_is_reachable():
    client = redis.Redis.from_url(env("REDIS_URL", default="redis://localhost:6379/0"))
    assert client.ping() is True
'@ | Set-Content -Path tests/test_redis.py -Encoding utf8
```

```powershell
docker compose -f infra/compose/docker-compose.yml up -d redis
uv run python -m pytest tests/test_redis.py
```

**Check**: smoke test passes against the Compose Redis container.

```powershell
git add -A
git commit -m "chore: add Redis cache configuration"
```

---

## Step 11 — Add RabbitMQ and a bare Celery app

Add a `rabbitmq` service to `docker-compose.yml` (same manual-edit approach
as Step 10's note) — image `rabbitmq:3-management`, ports `5672:5672` and
`15672:15672`, volume `rabbitmq_data:/var/lib/rabbitmq`, healthcheck
`rabbitmq-diagnostics -q ping`.

```powershell
@'
"""Celery app bound to Django settings.

`task_ignore_result=True` by default: the domain's asynchronous work follows
the transactional-outbox pattern (ADR-0004) — dispatchers/consumers act on
committed events and don't need callers to poll a result backend.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("be_py_eco")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(name="ping_task", ignore_result=False)
def ping_task():
    """Trivial no-op task proving worker<->broker<->result connectivity —
    not a real business task. See Issue #5, commit 11. `ignore_result=False`
    overrides the CELERY_TASK_IGNORE_RESULT default only for this smoke
    task, so the round-trip can be asserted in tests."""
    return "pong"
'@ | Set-Content -Path src/config/celery.py -Encoding utf8
```

Register `django_celery_beat` and `storages` won't come until Step 13 — for
now just add `django_celery_beat` to `INSTALLED_APPS` in `base.py`, and add
the Celery settings:

```powershell
(Get-Content src/config/settings/base.py -Raw) -replace '"rest_framework",', "`"rest_framework`",`n    `"django_celery_beat`"," | Set-Content src/config/settings/base.py -Encoding utf8

Add-Content -Path src/config/settings/base.py -Value @'

# Celery — broker is RabbitMQ. task_ignore_result=True: see config/celery.py.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@localhost:5672//")
# A result backend is configured so `ping_task` (above) can prove the
# worker<->broker<->result round-trip; real business tasks stay
# ignore_result=True (the CELERY_TASK_IGNORE_RESULT default) since they
# follow the transactional-outbox pattern (ADR-0004) and don't poll a result.
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = "UTC"  # matches TIME_ZONE below
'@
```

```powershell
Add-Content -Path .env -Value "CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//"
Add-Content -Path .env.example -Value "CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//"
```

Register the pytest plugin that provides the `celery_worker` fixture:

```powershell
@'
import celery.contrib.testing.tasks  # noqa: F401 — registers "celery.ping" for celery_worker's readiness check

pytest_plugins = ("celery.contrib.pytest",)
'@ | Set-Content -Path tests/conftest.py -Encoding utf8
```

```powershell
@'
"""Celery worker<->broker<->result round-trip smoke test.

Uses Celery's pytest plugin `celery_worker` fixture (registered in
tests/conftest.py) to spin up a real worker thread against the actual
RabbitMQ broker + Redis result backend for the duration of this test —
proving the connectivity path end to end without a separately-started
worker process.
"""

import time

import pytest

from config.celery import app, ping_task


@pytest.fixture
def celery_config():
    return {
        "broker_url": app.conf.broker_url,
        "result_backend": app.conf.result_backend,
    }


@pytest.fixture
def celery_app(celery_config):
    app.conf.update(**celery_config)
    return app


@pytest.fixture
def celery_worker_parameters():
    # Skip celery's own built-in "celery.ping" self-check — its result
    # fetch is flaky against this environment's Redis backend even when
    # the task itself completes; we prove the round-trip with our own
    # task + polling loop below instead.
    return {"perform_ping_check": False}


@pytest.mark.django_db
def test_ping_task_round_trips_through_broker(celery_worker):
    result = ping_task.delay()

    deadline = time.monotonic() + 10
    while not result.ready() and time.monotonic() < deadline:
        time.sleep(0.2)

    assert result.successful(), f"task did not complete in time (state={result.state})"
    assert result.result == "pong"
'@ | Set-Content -Path tests/test_celery.py -Encoding utf8
```

```powershell
docker compose -f infra/compose/docker-compose.yml up -d rabbitmq
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py migrate
uv run python -m pytest tests/test_celery.py
```

The integration test above runs a real worker thread for the test's
duration — no separately-started worker process needed. To watch a worker
running continuously instead, in a **separate PowerShell window**:

```powershell
$env:PYTHONPATH = "src"
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python -m celery -A config worker --loglevel=info --pool=solo
```

> Windows notes: `celery`'s own CLI executable can hit the same Application
> Control block as `pytest`/`mypy` — use `uv run python -m celery ...`. The
> `--pool=solo` flag is needed because Celery's default prefork pool doesn't
> work on Windows.

**Check**: `pytest tests/test_celery.py` passes — proving the
worker↔broker↔result round-trip for `ping_task.delay()`.

```powershell
git add -A
git commit -m "chore: add RabbitMQ and bare Celery app"
```

---

## Step 12 — Add OpenSearch to the environment

Add an `opensearch` service to `docker-compose.yml` (manual-edit approach) —
image `opensearchproject/opensearch:2`, env `discovery.type: single-node`,
`DISABLE_SECURITY_PLUGIN: "true"`, port `9200:9200`, volume
`opensearch_data:/usr/share/opensearch/data`, healthcheck
`curl -sf http://localhost:9200 || exit 1`.

```powershell
New-Item -ItemType Directory -Force -Path src/integrations/opensearch | Out-Null
New-Item -ItemType File -Force -Path src/integrations/opensearch/__init__.py | Out-Null
```

```powershell
@'
"""Thin factory for an opensearch-py client, configured from the environment.

No Django app wraps OpenSearch directly (unlike MinIO, which goes through
django-storages) — the `search` module (Slice 3) will build on this factory.
"""

import environ
from opensearchpy import OpenSearch

env = environ.Env()


def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[env("OPENSEARCH_URL", default="http://localhost:9200")],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )
'@ | Set-Content -Path src/integrations/opensearch/client.py -Encoding utf8
```

```powershell
@'
from integrations.opensearch.client import get_opensearch_client


def test_opensearch_is_reachable():
    client = get_opensearch_client()
    assert client.ping() is True
'@ | Set-Content -Path tests/test_opensearch.py -Encoding utf8
```

```powershell
Add-Content -Path .env -Value "OPENSEARCH_URL=http://localhost:9200"
Add-Content -Path .env.example -Value "OPENSEARCH_URL=http://localhost:9200"
```

```powershell
docker compose -f infra/compose/docker-compose.yml up -d opensearch
uv run python -m pytest tests/test_opensearch.py
```

**Check**: smoke test passes against the Compose OpenSearch container.

```powershell
git add -A
git commit -m "chore: add OpenSearch client and compose service"
```

---

## Step 13 — Add MinIO and the storage backend

Add a `minio` service to `docker-compose.yml` (manual-edit approach) — image
`minio/minio:latest`, command `server /data --console-address ":9001"`, env
`MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` (default `minioadmin`/`minioadmin`),
ports `9000:9000` and `9001:9001`, volume `minio_data:/data`, healthcheck
`mc ready local`.

Add `storages` to `INSTALLED_APPS` and the S3 settings to `base.py`:

```powershell
(Get-Content src/config/settings/base.py -Raw) -replace '"django_celery_beat",', "`"django_celery_beat`",`n    `"storages`"," | Set-Content src/config/settings/base.py -Encoding utf8

Add-Content -Path src/config/settings/base.py -Value @'

# MinIO (S3-compatible) via django-storages — the existing abstraction media
# will consume in Slice 2, rather than a custom client wrapper.
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="minioadmin")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="be-py-eco-local")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="http://localhost:9000")
AWS_S3_ADDRESSING_STYLE = "path"
'@
```

```powershell
Add-Content -Path .env -Value @'
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=be-py-eco-local
AWS_S3_ENDPOINT_URL=http://localhost:9000
'@
Add-Content -Path .env.example -Value @'
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=be-py-eco-local
AWS_S3_ENDPOINT_URL=http://localhost:9000
'@
```

```powershell
@'
import uuid

import boto3
import environ
import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage

env = environ.Env()


@pytest.fixture(autouse=True)
def _ensure_bucket_exists():
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    try:
        client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)


def test_storage_put_read_delete_round_trip():
    key = f"smoke/{uuid.uuid4()}.txt"
    content = b"slice-0 storage smoke test"

    from django.core.files.base import ContentFile

    saved_name = default_storage.save(key, ContentFile(content))
    try:
        with default_storage.open(saved_name) as f:
            assert f.read() == content
    finally:
        default_storage.delete(saved_name)

    assert not default_storage.exists(saved_name)
'@ | Set-Content -Path tests/test_storage.py -Encoding utf8
```

```powershell
docker compose -f infra/compose/docker-compose.yml up -d minio
uv run python -m pytest tests/test_storage.py
```

**Check**: smoke test passes against the Compose MinIO container (the fixture
creates the bucket on first run if it doesn't exist yet).

```powershell
git add -A
git commit -m "chore: add MinIO and django-storages S3 backend"
```

---

## Step 14 — Add the GitHub Actions CI workflow

```powershell
New-Item -ItemType Directory -Force -Path .github/workflows | Out-Null
```

Create `.github/workflows/ci.yml` — checkout → set up `uv` → `uv sync` →
`uv lock --check` → `manage.py check --database default` (against a Postgres
service container) → `pytest` (against Postgres + Redis + RabbitMQ +
OpenSearch + MinIO service containers) → `ruff check`/`format --check` →
`mypy`. See the committed file for the full service-container definitions
(too long to usefully retype here — copy it from the repo rather than
hand-typing five services' worth of health-check config).

```powershell
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"
git add -A
git commit -m "chore: add CI workflow"
```

**Check**: after pushing (Step 17 covers the push), the CI run is green on
GitHub Actions.

---

## Step 15 — Add supply-chain and secret-scanning gates to CI

```powershell
uv run python -m pip_audit
uv run python -m bandit -r src
uv run python -m detect_secrets scan --exclude-files '\.venv' --exclude-files '\.agents' --exclude-files '\.claude' > .secrets.baseline
```

`--exclude-files` skips the vendored `.agents`/`.claude` skill docs (same
reason as the ruff exclude in Step 7). If any findings remain (e.g. the
dev-only placeholder credentials in `.env.example`/`ci.yml`), open
`.secrets.baseline` and mark each as `"is_secret": false` — that's the
non-interactive equivalent of running `detect-secrets audit .secrets.baseline`
and pressing "n" for each one.

Add matching `pip-audit`/`bandit`/`detect-secrets` steps to `ci.yml` (see the
committed file).

**Check**: no unaddressed high-severity finding; CI stays green after pushing.

```powershell
git add -A
git commit -m "chore: add supply-chain and secret scanning to CI"
```

---

## Step 16 — Add the container build

```powershell
New-Item -ItemType Directory -Force -Path infra/docker | Out-Null
```

```powershell
@'
# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies first (separate layer, cached across code-only changes).
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

# Now copy the rest of the project and install it.
COPY . .
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000

# No production WSGI server (gunicorn/uvicorn) is pinned in this slice —
# guild.md §8's dependency list doesn't call for one yet, and choosing one
# is a decision for whichever slice first needs to actually serve traffic.
# manage.py runserver is good enough to prove the image builds and boots.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
'@ | Set-Content -Path infra/docker/Dockerfile -Encoding utf8
```

```powershell
@'
.venv/
.git/
__pycache__/
*.pyc
.env
.idea/
.agents/
.claude/
docs/
'@ | Set-Content -Path .dockerignore -Encoding utf8
```

```powershell
docker build -f infra/docker/Dockerfile -t be-py-eco:local .
```

**Check**: `docker build` succeeds locally and in CI. Sanity-check the image
actually boots (should fail cleanly asking for `SECRET_KEY` if none is
passed — that's `django-environ` doing its job, not a bug):

```powershell
docker run --rm be-py-eco:local python manage.py check --settings=config.settings.base
docker run --rm -e SECRET_KEY=test -e DATABASE_URL=psql://x:x@localhost:5432/x be-py-eco:local python manage.py check --settings=config.settings.base
```

```powershell
git add -A
git commit -m "chore: add container build"
```

---

## Step 17 — Document local setup

Add a "Getting started" section to the repo `README.md` covering:
`uv python install`, `docker compose up`, `uv sync`,
`manage.py check --database default`, `manage.py migrate`, `uv run pytest` —
the exact commands verified above (see the committed `README.md`).

**Check**: following the README from a fresh clone requires no undocumented step.

```powershell
git add -A
git commit -m "docs: add getting started section to README"
```

---

## After all steps pass

Push the branch and open the PR against `dev`:

```powershell
git push -u origin chore/setup-runbook
gh pr create --base dev --fill
```

Link the issue (`Closes #5`) and confirm every checkbox in Issue #5's
Acceptance Criteria is satisfied before requesting review.
