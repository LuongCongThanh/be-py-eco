from django.urls import path

from modules.search.api.storefront.views import ProductSearchView

urlpatterns = [
    path("products/search", ProductSearchView.as_view(), name="storefront-product-search"),
]
