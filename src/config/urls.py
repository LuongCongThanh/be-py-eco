"""URL configuration for the be-py-eco project."""

from django.urls import URLPattern, URLResolver, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
]
