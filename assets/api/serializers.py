"""
Serializers for assets API
"""
from rest_framework import serializers
from assets.models import (
    Materiel, Departement, Categorie, Client, Attribution,
    Alerte, HistoriqueAttribution
)


class DepartementSerializer(serializers.ModelSerializer):
    """Serializer for Departement"""
    class Meta:
        model = Departement
        fields = ['id', 'nom', 'code', 'description', 'date_creation']


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer for Categorie"""
    departement = DepartementSerializer(read_only=True)
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description', 'departement', 'date_creation']


class MaterielSerializer(serializers.ModelSerializer):
    """Serializer for Materiel"""
    categorie = CategorieSerializer(read_only=True)
    departement = DepartementSerializer(read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Materiel
        fields = [
            'id', 'asset_id', 'numero_inventaire', 'nom', 'description',
            'categorie', 'marque', 'modele', 'numero_serie',
            'etat_technique', 'statut_disponibilite', 'departement',
            'date_achat', 'prix', 'qr_code_url', 'notes',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['asset_id', 'numero_inventaire', 'date_creation', 'date_modification']
    
    def get_qr_code_url(self, obj):
        """Get QR code URL"""
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client"""
    departement = DepartementSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'nom', 'type_client', 'email', 'telephone',
            'numero_chambre', 'nom_evenement', 'date_arrivee',
            'date_depart', 'departement', 'notes',
            'date_creation', 'date_modification'
        ]


class AttributionSerializer(serializers.ModelSerializer):
    """Serializer for Attribution"""
    materiel = MaterielSerializer(read_only=True)
    client = ClientSerializer(read_only=True)
    employe_responsable = serializers.StringRelatedField(read_only=True)
    departement = DepartementSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Attribution
        fields = [
            'id', 'materiel', 'client', 'employe_responsable',
            'departement', 'date_attribution', 'date_retour_prevue',
            'date_retour_effective', 'motif', 'notes', 'is_overdue'
        ]
    
    def get_is_overdue(self, obj):
        """Check if attribution is overdue"""
        from django.utils import timezone
        if obj.date_retour_effective:
            return False
        return obj.date_retour_prevue < timezone.now().date()


class AlerteSerializer(serializers.ModelSerializer):
    """Serializer for Alerte"""
    materiel = MaterielSerializer(read_only=True)
    attribution = AttributionSerializer(read_only=True)
    departement = DepartementSerializer(read_only=True)
    
    class Meta:
        model = Alerte
        fields = [
            'id', 'type_alerte', 'severite', 'materiel', 'attribution',
            'departement', 'description', 'reglementee', 'date_creation'
        ]


class HistoriqueAttributionSerializer(serializers.ModelSerializer):
    """Serializer for HistoriqueAttribution"""
    attribution = AttributionSerializer(read_only=True)
    utilisateur = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = HistoriqueAttribution
        fields = [
            'id', 'attribution', 'action', 'utilisateur',
            'etat_avant', 'etat_apres', 'notes', 'date_action'
        ]

