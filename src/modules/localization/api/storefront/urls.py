from django.urls import path

from modules.localization.api.storefront.views import LocaleSuggestionView

urlpatterns = [
    path("suggestion", LocaleSuggestionView.as_view(), name="localization-suggestion"),
]
