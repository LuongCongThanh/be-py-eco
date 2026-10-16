from django.urls import path

from modules.search.api.storefront.views import ProductAutocompleteView, ProductSearchView

urlpatterns = [
    path("products/search", ProductSearchView.as_view(), name="storefront-product-search"),
    path(
        "products/autocomplete",
        ProductAutocompleteView.as_view(),
        name="storefront-product-autocomplete",
    ),
]
