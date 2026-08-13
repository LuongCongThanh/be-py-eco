# Setup Runbook — Slice 0 (Issue #5)

Manual, step-by-step execution guide for standing up the repository skeleton
described in [Issue #5](https://github.com/LuongCongThanh/be-py-eco/issues/5).
Each step below maps 1:1 to a commit in that issue's plan, in the same order.
Commands are written for **PowerShell** on Windows.

Note: unlike Issue #5's original layout (which nests everything under a
`backend/` subfolder), this runbook installs the Django project **directly at
the repo root** — `./pyproject.toml`, `./src/config/...`, `./manage.py`,
`./tests/...`, no `backend/` prefix anywhere.

Note: on this machine, a Windows Application Control (WDAC/AppLocker-style)
policy blocks spawning `pytest.exe`/`mypy.exe` directly — use `uv run python
-m pytest` (works) instead of `uv run pytest`. `mypy` is blocked even via
`python -m mypy` (its compiled extension DLL is blocked too); if that's also
the case for you, treat `mypy` as CI-only until IT allowlists it locally.

How to use this document:

- Work through the steps in order — each one assumes the previous steps are done.
- Run the commands, confirm the check passes, then commit before moving on.
- All commands are run from the repo root.

---

## Step 0 — Upgrade to Python 3.13

`pyproject.toml` (added in Step 1) pins `>=3.13,<3.14`. The machine currently
has Python 3.12.10, so install 3.13 via `uv` first.

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
uv add django==5.2.17 djangorestframework==3.18.0 psycopg==3.3.4 django-environ==0.14.0 django-filter==26.1 drf-spectacular==0.30.0 drf-standardized-errors==0.16.0 django-cors-headers==4.9.0
uv add djangorestframework-simplejwt==5.5.1 django-allauth==65.19.0 django-otp==1.7.0 django-axes==8.3.1 argon2-cffi==25.1.0 cryptography==50.0.0 django-countries==9.0.0 phonenumberslite==9.0.36
uv add celery==5.6.3 django-celery-beat==2.9.0 redis==8.1.0 opensearch-py==3.2.0 httpx==0.28.1 tenacity==9.1.4
uv add django-storages==1.14.6 boto3==1.43.69 Pillow==12.3.0 filetype==1.2.0
uv add structlog==26.1.0 sentry-sdk==2.67.1 prometheus-client==0.26.0
uv add --group dev pytest==9.1.1 pytest-django==4.14.0 pytest-cov==7.1.0 factory-boy==3.3.3 hypothesis==6.165.3 freezegun==1.5.5 respx==0.23.1
uv add --group dev ruff==0.16.2 mypy==2.3.0 django-stubs==6.0.9 pip-audit==2.10.1 bandit==1.9.4 detect-secrets==1.5.0
```

Add to `.gitignore` (repo root): `.venv/`, `__pycache__/`, `*.pyc`, `.env`.

**Check**: `uv sync` completes with no resolution errors.

```powershell
uv sync
git add -A
git commit -m "chore: add pinned dependency manifest"
```

---

## Step 2 — Add the local Docker Compose environment (PostgreSQL only)

Create `infra/compose/docker-compose.yml` with a `postgres` service (PostgreSQL
16) and a named volume. Create `.env.example` (repo root) with `DATABASE_URL`,
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. Copy it to `.env` for local use.

> Port note: if the machine already has a native PostgreSQL Windows service
> bound to port 5432 (`Get-Service *postgres*`), the Compose container will
> silently lose that port to it and Django will connect to the wrong server.
> Map the container to a different host port instead (e.g. `"5433:5432"`)
> and point `DATABASE_URL` at that port — no need to touch the native service.

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

Add `manage.py`, `src/config/{urls.py,wsgi.py,asgi.py}`, and
`src/config/settings/base.py` (env-driven, no `DATABASES` yet).

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.base"
uv run python manage.py check
```

**Check**: command fails with an error mentioning no `DATABASES` configured —
that failure is expected and proves settings/env wiring already works.

```powershell
git add -A
git commit -m "chore: bootstrap Django project skeleton"
```

---

## Step 4 — Wire the database connection

Add `DATABASES` to `base.py` (psycopg 3.x backend via `env.db_url("DATABASE_URL")`).
Add `config/settings/local.py`, `config/settings/test.py`, `config/settings/production.py`.

> Windows note: plain `psycopg==3.3.4` fails to import with
> `no pq wrapper available` because there's no system `libpq` on Windows by
> default. Use `psycopg[binary]==3.3.4` instead (`uv remove psycopg && uv add
> "psycopg[binary]==3.3.4"`), which bundles a prebuilt libpq.

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
docker exec -it <postgres-container-name> psql -U <user> -d <db> -c "\dt"
```

**Check**: migration reports success; `\dt` lists Django's built-in tables
(`auth_user`, `django_session`, etc.).

```powershell
git add -A
git commit -m "chore: run initial Django migration"
```

---

## Step 6 — Wire pytest against a real PostgreSQL test database

Add `[tool.pytest.ini_options]` to `pyproject.toml`
(`DJANGO_SETTINGS_MODULE=config.settings.test`). Add
`tests/test_environment.py` with a DB connectivity smoke test.

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

Add `[tool.ruff]` to `pyproject.toml`, with `extend-exclude = [".agents", ".claude"]`
(this repo vendors agent-skill docs under those dirs, and some of their
example assets are intentionally-incomplete Python templates that ruff can't
parse — exclude them rather than fixing them).

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

Add `[tool.mypy]` + `django-stubs` plugin, `DJANGO_SETTINGS_MODULE` pointed at
`config.settings.test`.

```powershell
uv run python -m mypy src
```

**Check**: exits clean, no type errors on the current skeleton.

```powershell
git add -A
git commit -m "chore: add mypy static type checking"
```

---

## Step 9 — Add the `common/` package skeleton

Create `common/{api,auth,db,money,ids,observability,testing}/__init__.py`.
Implement `common/ids` (UUIDv7 generator) with a unit test. Wire `structlog`
JSON logging into `LOGGING` in `base.py`.

```powershell
uv run python -m pytest
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py check
```

**Check**: pytest passes (including the new `common/ids` test); `manage.py check`
output includes at least one structured JSON log line.

```powershell
git add -A
git commit -m "chore: add common package skeleton with ids and logging"
```

---

## Step 10 — Add Redis to the environment

Add a `redis` service to `docker-compose.yml`. Add `CACHES` in `base.py`.
Add a smoke test opening a `redis.Redis.from_url(...)` connection and calling `.ping()`.

```powershell
docker compose -f infra/compose/docker-compose.yml up -d redis
uv run python -m pytest tests/ -k redis
```

**Check**: smoke test passes against the Compose Redis container.

```powershell
git add -A
git commit -m "chore: add Redis cache configuration"
```

---

## Step 11 — Add RabbitMQ and a bare Celery app

Add a `rabbitmq` service to `docker-compose.yml`. Add `src/config/celery.py`.
Register `django_celery_beat`, run its migration. Add a trivial `ping_task`.

```powershell
docker compose -f infra/compose/docker-compose.yml up -d rabbitmq
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py migrate
```

In a **separate PowerShell window** (keep it running, foreground, to watch logs):

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run celery -A config worker --loglevel=info
```

Back in the original window:

```powershell
uv run python -m pytest tests/ -k celery
```

**Check**: the worker window shows a successful connection to RabbitMQ; the
integration test dispatching `ping_task.delay()` passes.

```powershell
git add -A
git commit -m "chore: add RabbitMQ and bare Celery app"
```

---

## Step 12 — Add OpenSearch to the environment

Add an `opensearch` service (single-node, security disabled) to
`docker-compose.yml`. Add `integrations/opensearch/client.py`. Add a smoke test
calling `.info()`/`.ping()`.

```powershell
docker compose -f infra/compose/docker-compose.yml up -d opensearch
uv run python -m pytest tests/ -k opensearch
```

**Check**: smoke test passes against the Compose OpenSearch container.

```powershell
git add -A
git commit -m "chore: add OpenSearch client and compose service"
```

---

## Step 13 — Add MinIO and the storage backend

Add a `minio` service to `docker-compose.yml`. Configure `django-storages`
(S3 backend) pointed at MinIO via env vars. Add a smoke test that puts, reads
back, and deletes a small object.

```powershell
docker compose -f infra/compose/docker-compose.yml up -d minio
uv run python -m pytest tests/ -k storage
```

**Check**: smoke test passes against the Compose MinIO container.

```powershell
git add -A
git commit -m "chore: add MinIO and django-storages S3 backend"
```

---

## Step 14 — Add the GitHub Actions CI workflow

Add `.github/workflows/ci.yml`: checkout → set up `uv` → `uv sync` → Postgres
service container → `uv run python -m pytest` → `ruff check`/`format --check` → `mypy` →
`uv lock --check`.

```powershell
git add -A
git commit -m "chore: add CI workflow"
git push -u origin chore/setup-runbook
```

**Check**: open the PR (or push to the branch) and confirm the CI run is green
on GitHub Actions.

---

## Step 15 — Add supply-chain and secret-scanning gates to CI

Add `pip-audit`, `bandit`, `detect-secrets` steps to `ci.yml`. Generate `.secrets.baseline`.

```powershell
uv run pip-audit
uv run bandit -r src
uv run detect-secrets scan > .secrets.baseline
```

**Check**: no unaddressed high-severity finding; CI stays green after pushing.

```powershell
git add -A
git commit -m "chore: add supply-chain and secret scanning to CI"
```

---

## Step 16 — Add the container build

Add a multi-stage `Dockerfile` (using `uv`) under `infra/docker/Dockerfile`.
Add a CI job that builds it.

```powershell
docker build -f infra/docker/Dockerfile -t be-py-eco:local .
```

**Check**: `docker build` succeeds locally and in CI.

```powershell
git add -A
git commit -m "chore: add container build"
```

---

## Step 17 — Document local setup

Add a "Getting started" section to the repo `README.md`: `docker compose up`,
`uv sync`, `manage.py migrate`, `uv run python -m pytest` — the exact commands verified above.

**Check**: following the README from a fresh clone requires no undocumented step.

```powershell
git add -A
git commit -m "docs: add getting started section to README"
git push
```

---

## After all steps pass

Open the PR against `dev` and link the issue:

```powershell
gh pr create --base dev --fill
```

Confirm every checkbox in Issue #5's Acceptance Criteria is satisfied before
requesting review.
