from django.contrib import admin
from .models import Departement, Categorie, Materiel, Client, Attribution, HistoriqueAttribution, Alerte


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('code', 'nom')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'nom', 'description')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'departement', 'date_creation')
    list_filter = ('departement', 'date_creation')
    search_fields = ('nom', 'departement__nom')
    readonly_fields = ('date_creation',)
    
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'description', 'departement')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = ('asset_id', 'nom', 'departement', 'etat_technique', 'statut_disponibilite', 'date_creation')
    list_filter = ('departement', 'etat_technique', 'statut_disponibilite', 'date_creation')
    search_fields = ('asset_id', 'numero_inventaire', 'nom', 'marque')
    readonly_fields = ('qr_code', 'date_creation', 'date_modification')
    
    fieldsets = (
        ('Identifiants', {
            'fields': ('asset_id', 'numero_inventaire')
        }),
        ('Informations générales', {
            'fields': ('nom', 'description', 'categorie', 'departement')
        }),
        ('Caractéristiques techniques', {
            'fields': ('marque', 'modele', 'numero_serie')
        }),
        ('État et disponibilité', {
            'fields': ('etat_technique', 'statut_disponibilite')
        }),
        ('Informations financières', {
            'fields': ('date_achat', 'prix')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_client', 'email', 'telephone', 'date_creation')
    list_filter = ('type_client', 'date_creation')
    search_fields = ('nom', 'email', 'telephone')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'type_client')
        }),
        ('Coordonnées', {
            'fields': ('email', 'telephone')
        }),
        ('Hébergement', {
            'fields': ('numero_chambre', 'date_arrivee', 'date_depart'),
            'classes': ('collapse',)
        }),
        ('Conférence/Événement', {
            'fields': ('nom_evenement',),
            'classes': ('collapse',)
        }),
        ('Interne', {
            'fields': ('departement',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attribution)
class AttributionAdmin(admin.ModelAdmin):
    list_display = ('materiel', 'client', 'departement', 'date_attribution', 'date_retour_prevue', 'date_retour_effective')
    list_filter = ('departement', 'date_attribution', 'date_retour_effective')
    search_fields = ('materiel__asset_id', 'client__nom', 'motif')
    readonly_fields = ('date_attribution', 'materiel', 'client')
    date_hierarchy = 'date_attribution'
    
    fieldsets = (
        ('Matériel et client', {
            'fields': ('materiel', 'client')
        }),
        ('Responsable et département', {
            'fields': ('employe_responsable', 'departement')
        }),
        ('Dates', {
            'fields': ('date_attribution', 'date_retour_prevue', 'date_retour_effective')
        }),
        ('Informations', {
            'fields': ('motif', 'notes')
        }),
    )


@admin.register(HistoriqueAttribution)
class HistoriqueAttributionAdmin(admin.ModelAdmin):
    list_display = ('attribution', 'action', 'utilisateur', 'date_action')
    list_filter = ('action', 'date_action', 'utilisateur')
    search_fields = ('attribution__materiel__asset_id', 'attribution__client__nom')
    readonly_fields = ('date_action', 'attribution', 'action', 'utilisateur')
    date_hierarchy = 'date_action'
    
    fieldsets = (
        ('Attribution', {
            'fields': ('attribution',)
        }),
        ('Action', {
            'fields': ('action', 'utilisateur', 'date_action')
        }),
        ('États', {
            'fields': ('etat_avant', 'etat_apres')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # L'historique ne doit pas être modifié manuellement
        return False

    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression d'historique
        return False


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ('get_type_icon', 'type_alerte', 'get_materiel_display', 'get_client_display', 'departement', 'get_severite_color', 'reglementee', 'date_creation')
    list_filter = ('type_alerte', 'severite', 'departement', 'reglementee', 'date_creation')
    search_fields = ('description', 'materiel__asset_id', 'materiel__nom', 'attribution__client__nom', 'departement__nom')
    readonly_fields = ('date_creation', 'materiel', 'attribution', 'departement')
    date_hierarchy = 'date_creation'
    ordering = ('-date_creation',)
    
    def get_type_icon(self, obj):
        icons = {'PERDU': '—', 'DEFECTUEUX': '—', 'RETARD': '—', 'STOCK_CRITIQUE': '—'}
        return icons.get(obj.type_alerte, '•')
    get_type_icon.short_description = 'Type'
    
    def get_materiel_display(self, obj):
        if obj.materiel:
            return f'{obj.materiel.asset_id}'
        return '-'
    get_materiel_display.short_description = 'Matériel'
    
    def get_client_display(self, obj):
        if obj.attribution and obj.attribution.client:
            return obj.attribution.client.nom
        return '-'
    get_client_display.short_description = 'Client'
    
    def get_severite_color(self, obj):
        return obj.get_severite_display()
    get_severite_color.short_description = 'Sévérité'
    
    fieldsets = (
        ('Type d\'alerte', {
            'fields': ('type_alerte', 'severite')
        }),
        ('Objet', {
            'fields': ('materiel', 'attribution', 'departement')
        }),
        ('Contenu', {
            'fields': ('description',)
        }),
        ('Statut', {
            'fields': ('reglementee',)
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    actions = ['marquer_comme_reglementee', 'marquer_comme_non_reglementee']

    def marquer_comme_reglementee(self, request, queryset):
        updated = queryset.update(reglementee=True)
        self.message_user(request, f'{updated} alerte(s) marquée(s) comme réglementée(s).')
    marquer_comme_reglementee.short_description = "✓ Marquer comme réglementées"
    
    def marquer_comme_non_reglementee(self, request, queryset):
        updated = queryset.update(reglementee=False)
        self.message_user(request, f'{updated} alerte(s) réouvertes.')
    marquer_comme_non_reglementee.short_description = "✕ Rouvrir les alertes"
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
