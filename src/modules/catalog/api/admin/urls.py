from django.urls import path

from modules.catalog.api.admin.views import CategoryDetailView, ProductPublishView

urlpatterns = [
    path(
        "categories/<uuid:category_id>",
        CategoryDetailView.as_view(),
        name="admin-category-detail",
    ),
    path(
        "products/<uuid:product_id>/publish",
        ProductPublishView.as_view(),
        name="admin-product-publish",
    ),
]
