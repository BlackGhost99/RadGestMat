# assets/services.py
"""
Service de détection et gestion des alertes
"""
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from .models import Alerte, Materiel, Attribution, Departement, Categorie


class AlerteService:
    """Service pour détecter et créer des alertes automatiquement"""
    
    # Configuration des seuils
    JOURS_AVANT_ALERTE_RETARD = 0  # Alerte dès le jour de la date de retour prévue
    JOURS_AVANT_ALERTE_PERDU = 30  # Matériel considéré perdu après 30 jours
    SEUIL_STOCK_CRITIQUE = 2  # Moins de 2 unités disponibles = stock critique (par nom d'équipement)
    
    @staticmethod
    def detecter_retards_retour():
        """Détecte les attributions avec retard de retour"""
        aujourdhui = timezone.now().date()
        attributions_en_retard = Attribution.objects.filter(
            date_retour_prevue__lt=aujourdhui,
            date_retour_effective__isnull=True
        ).select_related('materiel', 'client', 'departement')
        
        alertes_creees = []
        for attribution in attributions_en_retard:
            # Vérifier si une alerte existe déjà
            alerte_existante = Alerte.objects.filter(
                type_alerte=Alerte.TYPE_RETARD,
                attribution=attribution,
                reglementee=False
            ).first()
            
            if not alerte_existante:
                jours_retard = (aujourdhui - attribution.date_retour_prevue).days
                severite = Alerte.SEVERITE_CRITICAL if jours_retard > 7 else Alerte.SEVERITE_WARNING
                
                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_RETARD,
                    severite=severite,
                    materiel=attribution.materiel,
                    attribution=attribution,
                    departement=attribution.departement,
                    description=f"Retard de retour: {jours_retard} jour(s) de retard. "
                               f"Date retour prévue: {attribution.date_retour_prevue}. "
                               f"Client: {attribution.client.nom}"
                )
                alertes_creees.append(alerte)
        
        return alertes_creees
    
    @staticmethod
    def detecter_materiel_defectueux():
        """Détecte les matériels défectueux nécessitant attention"""
        materiels_defectueux = Materiel.objects.filter(
            etat_technique=Materiel.ETAT_DEFECTUEUX,
            statut_disponibilite__in=[Materiel.STATUT_DISPONIBLE, Materiel.STATUT_ATTRIBUE]
        ).select_related('departement')
        
        alertes_creees = []
        for materiel in materiels_defectueux:
            # Vérifier si une alerte existe déjà
            alerte_existante = Alerte.objects.filter(
                type_alerte=Alerte.TYPE_DEFECTUEUX,
                materiel=materiel,
                reglementee=False
            ).first()
            
            if not alerte_existante:
                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_DEFECTUEUX,
                    severite=Alerte.SEVERITE_WARNING,
                    materiel=materiel,
                    departement=materiel.departement,
                    description=f"Matériel défectueux nécessitant attention: {materiel.nom} "
                               f"({materiel.asset_id}). Statut: {materiel.get_statut_disponibilite_display()}"
                )
                alertes_creees.append(alerte)
        
        return alertes_creees
    
    @staticmethod
    def detecter_stock_critique():
        """
        Détecte les stocks critiques par nom d'équipement.
        Ex: Si on a 7 projecteurs vidéo et qu'il n'en reste que 2 disponibles, alerte.
        """
        alertes_creees = []
        
        # Grouper par nom d'équipement et département
        # On compte tous les matériels (disponibles, attribués, etc.) avec le même nom
        stocks_par_nom = Materiel.objects.values('nom', 'departement').annotate(
            total_materiels=Count('id')
        )
        
        for stock_info in stocks_par_nom:
            nom_equipement = stock_info['nom']
            departement_id = stock_info['departement']
            total_materiels = stock_info['total_materiels']
            
            try:
                departement = Departement.objects.get(id=departement_id)
            except Departement.DoesNotExist:
                continue
            
            # Compter les matériels disponibles (fonctionnels et disponibles)
            materiels_disponibles = Materiel.objects.filter(
                nom=nom_equipement,
                departement=departement,
                statut_disponibilite=Materiel.STATUT_DISPONIBLE,
                etat_technique=Materiel.ETAT_FONCTIONNEL
            ).count()
            
            # Vérifier si le stock disponible est critique (<= seuil)
            if materiels_disponibles <= AlerteService.SEUIL_STOCK_CRITIQUE:
                # Vérifier si une alerte existe déjà pour cet équipement/département
                alerte_existante = Alerte.objects.filter(
                    type_alerte=Alerte.TYPE_STOCK_CRITIQUE,
                    departement=departement,
                    reglementee=False,
                    description__icontains=nom_equipement
                ).first()
                
                if not alerte_existante:
                    alerte = Alerte.objects.create(
                        type_alerte=Alerte.TYPE_STOCK_CRITIQUE,
                        severite=Alerte.SEVERITE_WARNING,
                        departement=departement,
                        description=f"Stock critique pour l'équipement '{nom_equipement}': "
                                   f"{materiels_disponibles} unité(s) disponible(s) sur {total_materiels} total. "
                                   f"Seuil d'alerte: {AlerteService.SEUIL_STOCK_CRITIQUE} unité(s)"
                    )
                    alertes_creees.append(alerte)
        
        return alertes_creees
    
    @staticmethod
    def detecter_materiel_perdu():
        """Détecte les matériels perdus (non retournés après X jours)"""
        aujourdhui = timezone.now().date()
        date_limite = aujourdhui - timedelta(days=AlerteService.JOURS_AVANT_ALERTE_PERDU)
        
        attributions_perdues = Attribution.objects.filter(
            date_retour_prevue__lt=date_limite,
            date_retour_effective__isnull=True
        ).select_related('materiel', 'client', 'departement')
        
        alertes_creees = []
        for attribution in attributions_perdues:
            # Vérifier si une alerte existe déjà
            alerte_existante = Alerte.objects.filter(
                type_alerte=Alerte.TYPE_PERDU,
                attribution=attribution,
                reglementee=False
            ).first()
            
            if not alerte_existante:
                jours_ecoules = (aujourdhui - attribution.date_retour_prevue).days
                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_PERDU,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=attribution.materiel,
                    attribution=attribution,
                    departement=attribution.departement,
                    description=f"Matériel considéré comme perdu: {attribution.materiel.nom} "
                               f"({attribution.materiel.asset_id}). "
                               f"Non retourné depuis {jours_ecoules} jour(s). "
                               f"Client: {attribution.client.nom}. "
                               f"Date retour prévue: {attribution.date_retour_prevue}"
                )
                alertes_creees.append(alerte)
        
        return alertes_creees
    
    @classmethod
    def detecter_toutes_alertes(cls, envoyer_emails=True):
        """Détecte toutes les alertes et retourne un résumé"""
        from .email_service import EmailAlerteService
        
        resultats = {
            'retards': cls.detecter_retards_retour(),
            'defectueux': cls.detecter_materiel_defectueux(),
            'stock_critique': cls.detecter_stock_critique(),
            'perdus': cls.detecter_materiel_perdu(),
        }
        
        total = sum(len(v) for v in resultats.values())
        resultats['total'] = total
        
        # Envoyer des emails pour les alertes critiques
        if envoyer_emails:
            for alerte in resultats['retards'] + resultats['perdus']:
                if alerte.severite == Alerte.SEVERITE_CRITICAL:
                    EmailAlerteService.envoyer_alerte_critique(alerte)
        
        return resultats
    
    @staticmethod
    def get_alertes_non_reglementees(departement=None):
        """Récupère toutes les alertes non réglées, optionnellement filtrées par département"""
        queryset = Alerte.objects.filter(reglementee=False).select_related(
            'materiel', 'attribution__client', 'departement'
        )
        
        if departement:
            queryset = queryset.filter(departement=departement)
        
        return queryset.order_by('-severite', '-date_creation')
    
    @staticmethod
    def get_nombre_alertes_critiques(departement=None):
        """Retourne le nombre d'alertes critiques non réglées"""
        queryset = Alerte.objects.filter(
            reglementee=False,
            severite=Alerte.SEVERITE_CRITICAL
        )
        
        if departement:
            queryset = queryset.filter(departement=departement)
        
        return queryset.count()

