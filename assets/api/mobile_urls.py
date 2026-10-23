"""URL configuration for the limited mobile API surface."""
from django.urls import path

from assets.api.mobile import MobileAssetDetailView, MobileAssetListView

app_name = "mobile_api"

urlpatterns = [
    path("assets/", MobileAssetListView.as_view(), name="asset-list"),
    path("assets/<str:asset_id>/", MobileAssetDetailView.as_view(), name="asset-detail"),
]
