"""
API URLs for assets
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assets.api.views import (
    DepartementViewSet, CategorieViewSet, MaterielViewSet,
    ClientViewSet, AttributionViewSet, AlerteViewSet,
    HistoriqueAttributionViewSet
)

router = DefaultRouter()
router.register(r'departements', DepartementViewSet, basename='departement')
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'materiels', MaterielViewSet, basename='materiel')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'attributions', AttributionViewSet, basename='attribution')
router.register(r'alertes', AlerteViewSet, basename='alerte')
router.register(r'historiques', HistoriqueAttributionViewSet, basename='historique')

urlpatterns = [
    path('', include(router.urls)),
]

