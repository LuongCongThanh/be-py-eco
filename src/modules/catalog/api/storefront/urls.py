from django.urls import path

from modules.catalog.api.storefront.views import ProductDetailView, ProductListView

urlpatterns = [
    path("products", ProductListView.as_view(), name="storefront-product-list"),
    path(
        "products/<uuid:product_id>",
        ProductDetailView.as_view(),
        name="storefront-product-detail",
    ),
]
