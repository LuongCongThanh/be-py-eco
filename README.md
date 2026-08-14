# be-py-eco

Django/DRF backend for be-py-eco — a modular monolith (one Django deployment,
one PostgreSQL cluster, clearly separated business modules). See
[CONTEXT.md](CONTEXT.md) for the domain glossary, [guild.md](guild.md) for
the full technical spec, and [docs/adr/](docs/adr/) for architecture
decisions.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package/environment manager)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (local
  PostgreSQL, Redis, RabbitMQ, OpenSearch, MinIO via Docker Compose)
- `gh` CLI, if you'll be opening PRs from the command line

## Getting started

```powershell
# 1. Python toolchain
uv python install 3.13

# 2. Local infrastructure (PostgreSQL, Redis, RabbitMQ, OpenSearch, MinIO)
copy .env.example .env
docker compose -f infra/compose/docker-compose.yml up -d

# 3. Dependencies
uv sync

# 4. Confirm Django can reach Postgres, then apply the schema
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py check --database default
uv run python manage.py migrate

# 5. Test suite (real PostgreSQL, no SQLite — see guild.md §10.5)
uv run python -m pytest
```

> Windows note: if port 5432 is already taken by a native PostgreSQL install,
> remap the `postgres` service in `infra/compose/docker-compose.yml` to a
> free host port and update `DATABASE_URL` in `.env` to match — see
> `docs/agents/setup-runbook.md` Step 2 for details. This repo's own compose
> file already maps to `5433` instead of `5432` for exactly this reason.
>
> Also on Windows, `pytest`/`mypy`/`celery`'s own CLI executables can be
> blocked by an Application Control policy — use `uv run python -m <tool>`
> instead of `uv run <tool>` if that happens. `mypy` may stay blocked even
> via `python -m mypy` (its compiled extension DLL); treat it as CI-only
> until IT allowlists it.

### Alternative: native local PostgreSQL instead of the Compose container

If you already run PostgreSQL natively on the host (e.g. a Windows service
install on port `5432`) and would rather point Django at that instead of the
Compose `postgres` container, do this once per machine:

```powershell
# 1. Create the app role and database on the native instance (run as a
#    superuser, e.g. `postgres`).
psql -U postgres -h localhost -p 5432 -c "CREATE ROLE be_py_eco LOGIN PASSWORD 'be_py_eco' CREATEDB;"
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE be_py_eco OWNER be_py_eco;"

# 2. Point .env at the native instance instead of the container.
#    DATABASE_URL=psql://be_py_eco:be_py_eco@localhost:5432/be_py_eco

# 3. Stop the container so nobody accidentally connects to a stale one.
docker compose -f infra/compose/docker-compose.yml stop postgres
```

The `CREATEDB` grant is required because `pytest-django` creates and drops a
throwaway test database (`test_be_py_eco`) around the suite — a role without
it fails with `permission denied to create database`. Verify the switch with
`uv run python -m pytest tests/test_environment.py -k database_connection`.

Switching back to the container is just the reverse: restore
`DATABASE_URL`'s port to `5433` and `docker compose ... up -d postgres`.

## Everyday commands

```powershell
# Run the dev server
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python manage.py runserver

# Run the test suite
uv run python -m pytest

# Run one test file / one test
uv run python -m pytest tests/test_celery.py
uv run python -m pytest tests/test_celery.py::test_ping_task_round_trips_through_broker

# Lint and format (scoped to our own code — .agents/.claude are vendored skill docs)
uv run ruff check src tests manage.py
uv run ruff format src tests manage.py

# Static type check (see the Windows note above if this is blocked locally)
uv run python -m mypy src

# Dependency / security scans
uv run python -m pip_audit
uv run python -m bandit -r src -c pyproject.toml
uv run python -m detect_secrets scan --exclude-files '\.venv' --exclude-files '\.agents' --exclude-files '\.claude'

# Run a Celery worker manually (rarely needed — tests spin up their own via
# the celery_worker pytest fixture)
$env:PYTHONPATH = "src"
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"
uv run python -m celery -A config worker --loglevel=info --pool=solo

# Build the container image
docker build -f infra/docker/Dockerfile -t be-py-eco:local .

# Tear down local infrastructure
docker compose -f infra/compose/docker-compose.yml down
```

## Project layout

```text
be-py-eco/
|-- pyproject.toml, uv.lock, manage.py   # Python project + Django entrypoint
|-- src/
|   |-- config/          # settings/{base,local,test,production}.py, urls, celery, wsgi/asgi
|   |-- common/           # api, auth, db, money, ids, observability, testing
|   |-- modules/          # business modules land here from Slice 1 onward
|   `-- integrations/     # thin client factories (e.g. opensearch)
|-- tests/                 # mirrors src/ layout
|-- infra/
|   |-- compose/           # docker-compose.yml — local dev infra
|   `-- docker/            # Dockerfile — container build
|-- docs/
|   |-- adr/               # architecture decision records
|   |-- agents/            # agent-facing process docs (git workflow, this runbook, ...)
|   `-- api/               # openapi.yaml (lands in Slice 1)
`-- .github/workflows/      # CI
```

See [guild.md §7](guild.md) for the full rationale, and
[docs/agents/setup-runbook.md](docs/agents/setup-runbook.md) for exactly how
this skeleton was built, step by step, with copy-pasteable commands.

## CI

`.github/workflows/ci.yml` runs on every PR and push to `main`/`dev`:
lockfile check → DB connectivity check → full test suite (against real
Postgres/Redis/RabbitMQ/OpenSearch service containers, plus MinIO started
via a manual `docker run` step — GitHub Actions service containers can't
pass MinIO the `server /data` command it needs, and Bitnami's drop-in image
was retired from Docker Hub) → ruff → mypy → pip-audit → bandit →
detect-secrets → container build.

## Contributing

- Branching/commit/PR conventions: [docs/agents/git-workflow.md](docs/agents/git-workflow.md)
- Issue tracker conventions: [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md)
- Triage labels: [docs/agents/triage-labels.md](docs/agents/triage-labels.md)

## Status

This skeleton implements
[Issue #5 — Slice 0: Repository scaffolding, environment & tooling](https://github.com/LuongCongThanh/be-py-eco/issues/5).
No business/domain code exists yet — `src/modules/` is intentionally empty
until Slice 1.
