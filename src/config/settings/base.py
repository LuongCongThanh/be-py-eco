"""Base Django settings — shared, env-driven, no environment-specific defaults.

Every value is read from the environment via django-environ; nothing here
hard-codes a value that would work "by accident" in production.
"""

from datetime import timedelta
from pathlib import Path

import environ
import structlog

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

DATABASES = {
    "default": env.db_url("DATABASE_URL"),
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    },
}

# Celery — broker is RabbitMQ. task_ignore_result=True: see config/celery.py.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@localhost:5672//")
# A result backend is configured so `ping_task` (below) can prove the
# worker<->broker<->result round-trip; real business tasks stay
# ignore_result=True (the CELERY_TASK_IGNORE_RESULT default) since they
# follow the transactional-outbox pattern (ADR-0004) and don't poll a result.
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = "UTC"  # matches TIME_ZONE below

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

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "django_celery_beat",
    "django_countries",
    "storages",
    "common.db",
    "modules.accounts",
    "modules.audit",
    "modules.localization",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "common.observability.middleware.RequestIDMiddleware",
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

# Placeholder transactional email — templated/localized send is Slice 7.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@be-py-eco.local")

# integrations/google_oauth — adapter selected via config, per guild.md §7.6.
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")
GOOGLE_OAUTH_CLIENT_CLASS = env(
    "GOOGLE_OAUTH_CLIENT_CLASS",
    default="integrations.google_oauth.client.HttpGoogleOAuthClient",
)

# common/api — envelope + Problem Details error shape (guild.md §5.3/§5.4),
# established here so every later module reuses it unchanged.
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "common.api.exceptions.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": ["common.auth.authentication.JWTAuthentication"],
    # Placeholder rates for local dev/test only — guild.md §16 requires
    # concrete rate limits to be decided via a dedicated ticket, not
    # invented in code. Override per-environment via these env vars.
    "DEFAULT_THROTTLE_RATES": {
        "auth_ip": env("THROTTLE_RATE_AUTH_IP", default="20/min"),
        "auth_account": env("THROTTLE_RATE_AUTH_ACCOUNT", default="5/min"),
    },
}

# Customer JWTs: 10-15 min access, rotating/revocable refresh (guild.md §6.1).
# Refresh rotation + hashed session storage land in a later commit.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Argon2 first — guild.md §6.1. Django tries hashers in this order and
# upgrades existing hashes on next successful login (PBKDF2 kept as fallback
# for verifying already-hashed passwords, not for new ones).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# drf-spectacular — OpenAPI 3.1 schema at /api/v1/schema/, committed to
# docs/api/openapi.yaml (guild.md §5.7). SCHEMA_PATH_PREFIX groups tags by
# the first path segment after the version, e.g. /api/v1/storefront/products.
SPECTACULAR_SETTINGS = {
    "TITLE": "be-py-eco API",
    "DESCRIPTION": "E-commerce backend API for be-py-eco.",
    "VERSION": "1.0.0",
    "OAS_VERSION": "3.1.0",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "SERVE_INCLUDE_SCHEMA": False,
}

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
