from django.urls import path

from modules.catalog.api.admin.views import CategoryDetailView

urlpatterns = [
    path(
        "categories/<uuid:category_id>",
        CategoryDetailView.as_view(),
        name="admin-category-detail",
    ),
]
