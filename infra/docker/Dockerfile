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
