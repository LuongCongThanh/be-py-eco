from django.urls import path

from modules.pricing.api.admin.views import ExchangeRateListView

urlpatterns = [
    path("exchange-rates", ExchangeRateListView.as_view(), name="admin-exchange-rate-list"),
]
