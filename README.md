# be-py-eco

## Getting started

Prerequisites: [uv](https://docs.astral.sh/uv/), Docker Desktop.

```powershell
# 1. Python toolchain
uv python install 3.13

# 2. Local infrastructure (PostgreSQL, Redis, RabbitMQ, OpenSearch, MinIO)
copy .env.example .env
docker compose -f infra/compose/docker-compose.yml up -d

# 3. Dependencies
uv sync

# 4. Database schema
uv run python manage.py migrate

# 5. Test suite (real PostgreSQL, no SQLite — see guild.md §10.5)
uv run python -m pytest
```

> Windows note: if port 5432 is already taken by a native PostgreSQL install,
> remap the `postgres` service in `infra/compose/docker-compose.yml` to a
> free host port and update `DATABASE_URL` in `.env` to match — see
> `docs/agents/setup-runbook.md` Step 4 for details.
>
> Also on Windows, `pytest`/`mypy`/`celery`'s own CLI executables can be
> blocked by an Application Control policy — use `uv run python -m <tool>`
> instead of `uv run <tool>` if that happens.

For the full step-by-step build-up of this skeleton (with the reasoning
behind each piece), see [docs/agents/setup-runbook.md](docs/agents/setup-runbook.md)
and [Issue #5](https://github.com/LuongCongThanh/be-py-eco/issues/5).
