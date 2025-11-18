"""
API views for assets
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from assets.models import (
    Materiel, Departement, Categorie, Client, Attribution,
    Alerte, HistoriqueAttribution
)
from assets.api.serializers import (
    DepartementSerializer, CategorieSerializer, MaterielSerializer,
    ClientSerializer, AttributionSerializer, AlerteSerializer,
    HistoriqueAttributionSerializer
)
from assets.mixins import DepartmentMixin, SearchMixin, FilterMixin
from users.permissions import can_view_department


class DepartementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Departement"""
    queryset = Departement.objects.all()
    serializer_class = DepartementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'code']
    ordering_fields = ['nom', 'date_creation']
    ordering = ['nom']


class CategorieViewSet(viewsets.ModelViewSet):
    """ViewSet for Categorie"""
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'date_creation']
    ordering = ['nom']
    
    def get_queryset(self):
        """Filter by department"""
        queryset = super().get_queryset()
        departement = getattr(self.request, 'departement', None)
        if departement:
            queryset = queryset.filter(departement=departement)
        return queryset


class MaterielViewSet(viewsets.ModelViewSet):
    """ViewSet for Materiel"""
    queryset = Materiel.objects.select_related('categorie', 'departement')
    serializer_class = MaterielSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nom', 'asset_id', 'numero_inventaire', 'marque', 'modele', 'numero_serie']
    ordering_fields = ['date_creation', 'date_modification', 'nom']
    ordering = ['-date_creation']
    
    def get_queryset(self):
        """Filter by department"""
        queryset = super().get_queryset()
        departement = getattr(self.request, 'departement', None)
        if departement:
            queryset = queryset.filter(departement=departement)
        return queryset
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """Checkout material"""
        materiel = self.get_object()
        # Implementation for checkout
        return Response({'status': 'checkout initiated'})
    
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        """Checkin material"""
        materiel = self.get_object()
        # Implementation for checkin
        return Response({'status': 'checkin initiated'})


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for Client"""
    queryset = Client.objects.select_related('departement')
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nom', 'email', 'telephone']
    ordering_fields = ['date_creation', 'nom']
    ordering = ['-date_creation']
    
    def get_queryset(self):
        """Filter by department"""
        queryset = super().get_queryset()
        departement = getattr(self.request, 'departement', None)
        if departement:
            queryset = queryset.filter(departement=departement)
        return queryset


class AttributionViewSet(viewsets.ModelViewSet):
    """ViewSet for Attribution"""
    queryset = Attribution.objects.select_related(
        'materiel', 'client', 'employe_responsable', 'departement'
    )
    serializer_class = AttributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['client__nom', 'materiel__nom', 'materiel__asset_id']
    ordering_fields = ['date_attribution', 'date_retour_prevue']
    ordering = ['-date_attribution']
    
    def get_queryset(self):
        """Filter by department and status"""
        queryset = super().get_queryset()
        departement = getattr(self.request, 'departement', None)
        if departement:
            queryset = queryset.filter(departement=departement)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(date_retour_effective__isnull=True)
        elif status_filter == 'completed':
            queryset = queryset.filter(date_retour_effective__isnull=False)
        
        return queryset


class AlerteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Alerte"""
    queryset = Alerte.objects.select_related(
        'materiel', 'attribution', 'departement'
    )
    serializer_class = AlerteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['date_creation', 'severite']
    ordering = ['-severite', '-date_creation']
    
    def get_queryset(self):
        """Filter by department and unresolved"""
        queryset = super().get_queryset()
        departement = getattr(self.request, 'departement', None)
        if departement:
            queryset = queryset.filter(departement=departement)
        
        # Filter unresolved by default
        unresolved = self.request.query_params.get('unresolved', 'true')
        if unresolved.lower() == 'true':
            queryset = queryset.filter(reglementee=False)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark alert as resolved"""
        alerte = self.get_object()
        alerte.reglementee = True
        alerte.save()
        return Response({'status': 'alert marked as resolved'})


class HistoriqueAttributionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for HistoriqueAttribution"""
    queryset = HistoriqueAttribution.objects.select_related(
        'attribution', 'utilisateur'
    )
    serializer_class = HistoriqueAttributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ['date_action']
    ordering = ['-date_action']

