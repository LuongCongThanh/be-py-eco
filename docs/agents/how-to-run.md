# How to Run the Project

This is a step-by-step walkthrough of getting `be-py-eco` (a Django/DRF
modular monolith) running locally on Windows, and the commands you'll use
day-to-day afterwards. It complements the terse command lists in
[README.md](../../README.md) with the *why* behind each step.

For the original build-out of this scaffolding (how the skeleton itself was
assembled), see [setup-runbook.md](setup-runbook.md). This doc is about
running what already exists.

## 1. First-time setup

### 1.1 Install the Python toolchain via `uv`

```powershell
uv python install 3.13
```

The project is managed by [`uv`](https://docs.astral.sh/uv/) instead of
plain `pip`/`venv`. `uv` pins the exact Python version and resolves/locks
dependencies (`uv.lock`) so everyone — and CI — gets identical versions.

### 1.2 Start local infrastructure

```powershell
copy .env.example .env
docker compose -f infra/compose/docker-compose.yml up -d
```

This brings up PostgreSQL, Redis, RabbitMQ, OpenSearch, and MinIO in Docker
containers — the full set of backing services the app depends on locally.
`.env` holds connection strings/secrets for all of them; `.env.example` is
the template checked into git (never commit `.env` itself).

**Windows gotcha:** this repo's compose file maps Postgres to host port
**5433**, not the default 5432. That's deliberate — many Windows machines
already have a native PostgreSQL service occupying 5432, and this avoids a
port clash out of the box.

### 1.3 Install project dependencies

```powershell
uv sync
```

Reads `pyproject.toml`/`uv.lock` and installs everything into `.venv`,
exactly as locked — no surprise version drift between machines.

### 1.4 Point Django at the right settings, then verify + migrate

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py check --database default
uv run python manage.py migrate
```

- `DJANGO_SETTINGS_MODULE` selects which settings module under
  `src/config/settings/` to use (`local`, `test`, `production`, ...). It
  must be set in *every new shell* before running `manage.py` — it isn't
  persisted automatically.
- `check --database default` confirms Django can actually reach Postgres
  before you try anything else — fails fast with a clear error if the
  container isn't up or `.env` is misconfigured.
- `migrate` applies the schema.

### 1.5 Run the test suite once, to confirm the whole stack works

```powershell
uv run python -m pytest
```

Tests run against a **real PostgreSQL** database (a throwaway
`test_be_py_eco` DB created/dropped per run) — no SQLite shortcut. See
`guild.md §10.5` for the rationale. A green run here means setup succeeded.

> **Why `uv run python -m pytest` and not `uv run pytest`?** On Windows,
> Application Control policies can block `pytest`/`mypy`/`celery`'s own CLI
> executables. Routing through `python -m <tool>` avoids that. `mypy` can
> still be blocked even this way (its compiled extension DLL) — treat it as
> CI-only until IT allowlists it.

### 1.6 (Optional) Use a native PostgreSQL install instead of the container

If you already run PostgreSQL natively on the host (e.g. a Windows service
on port 5432) and would rather point Django at that instead of spinning up
the Compose container, do this once per machine:

```powershell
# 1. Create the app role and database (run as a superuser, e.g. `postgres`).
psql -U postgres -h localhost -p 5432 -c "CREATE ROLE be_py_eco LOGIN PASSWORD 'be_py_eco' CREATEDB;"
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE be_py_eco OWNER be_py_eco;"

# 2. Point .env at the native instance instead of the container.
#    DATABASE_URL=psql://be_py_eco:be_py_eco@localhost:5432/be_py_eco

# 3. Stop the container so nobody accidentally connects to a stale one.
docker compose -f infra/compose/docker-compose.yml stop postgres
```

Why `CREATEDB` specifically: `pytest-django` creates and drops the
`test_be_py_eco` database around every test run. Without that grant, tests
fail with `permission denied to create database`.

Verify the switch worked:

```powershell
uv run python -m pytest tests/test_environment.py -k database_connection
```

To switch back: restore `DATABASE_URL`'s port to `5433` and run
`docker compose -f infra/compose/docker-compose.yml up -d postgres`.

## 2. Everyday commands

Remember to set `DJANGO_SETTINGS_MODULE` in each new shell before any
`manage.py` command:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
```

### 2.1 Run the dev server

```powershell
uv run python manage.py runserver
```

### 2.2 Run tests

```powershell
# Whole suite
uv run python -m pytest

# One file
uv run python -m pytest tests/test_celery.py

# One specific test
uv run python -m pytest tests/test_celery.py::test_ping_task_round_trips_through_broker
```

### 2.3 Lint and format

```powershell
uv run ruff check src tests manage.py
uv run ruff format src tests manage.py
```

Scoped to `src`, `tests`, `manage.py` only — `.agents`/`.claude` are vendored
skill docs, not our code, and are excluded.

### 2.4 Static type check

```powershell
uv run python -m mypy src
```

May be blocked on Windows by Application Control (see the note in §1.5) —
if so, treat it as CI-only for now.

### 2.5 Dependency / security scans

```powershell
uv run python -m pip_audit
uv run python -m bandit -r src
uv run python -m detect_secrets scan --exclude-files '\.venv' --exclude-files '\.agents' --exclude-files '\.claude'
```

- `pip_audit` — checks installed dependencies against known CVEs.
- `bandit` — static analysis for common Python security issues.
- `detect_secrets` — scans for accidentally committed secrets.

### 2.6 Run a Celery worker manually

Rarely needed by hand — tests spin up their own worker automatically via the
`celery_worker` pytest fixture. Only do this if you need to manually exercise
async tasks against the running dev server:

```powershell
$env:PYTHONPATH = "src"
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python -m celery -A config worker --loglevel=info --pool=solo
```

`--pool=solo` is used because Celery's default worker pools don't play well
with Windows.

### 2.7 Build the container image

```powershell
docker build -f infra/docker/Dockerfile -t be-py-eco:local .
```

### 2.8 Tear down local infrastructure

```powershell
docker compose -f infra/compose/docker-compose.yml down
```

Stops and removes the Postgres/Redis/RabbitMQ/OpenSearch/MinIO containers.
Your `.env` and code are untouched — this only affects the running
containers.

## 3. What CI does on every PR/push

`.github/workflows/ci.yml` mirrors the commands above, in this order:
lockfile check → DB connectivity check → full test suite (against real
Postgres/Redis/RabbitMQ/OpenSearch service containers, plus MinIO started
via a manual `docker run` step) → ruff → mypy → pip-audit → bandit →
detect-secrets → container build.

If something passes locally but you're unsure it'll pass in CI, this list is
the checklist to run through manually before pushing.

## 4. Where to look next

- [README.md](../../README.md) — quick-reference command list and project layout
- [CONTEXT.md](../../CONTEXT.md) — domain glossary
- [guild.md](../../guild.md) — full technical spec
- [setup-runbook.md](setup-runbook.md) — how this scaffolding was originally built
- [git-workflow.md](git-workflow.md) — branching/commit/PR conventions
- [docs/adr/](../adr/) — architecture decision records
