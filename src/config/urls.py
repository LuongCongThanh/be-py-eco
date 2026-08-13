"""URL configuration for the be-py-eco project.

Empty for now — the `/api/v1/...` namespace and `/health/*` endpoints land
in Slice 1 (see Issue #5's "Explicit non-decisions" section).
"""

from django.urls import URLPattern, URLResolver

urlpatterns: list[URLPattern | URLResolver] = []
