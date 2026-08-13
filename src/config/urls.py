"""URL configuration for the be-py-eco project."""

from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.observability import health

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/storefront/accounts/", include("modules.accounts.api.storefront.urls")),
    path("api/v1/storefront/localization/", include("modules.localization.api.storefront.urls")),
    path("api/v1/admin/", include("modules.accounts.api.admin.urls")),
    path("health/live", health.live, name="health-live"),
    path("health/ready", health.ready, name="health-ready"),
]
