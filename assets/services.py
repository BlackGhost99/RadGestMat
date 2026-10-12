# assets/services.py
"""
Service de détection et gestion des alertes
"""
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField, Value
from datetime import timedelta
from .models import Alerte, Materiel, Attribution, Departement, Categorie


class AlerteService:
    """Service pour détecter et créer des alertes automatiquement"""
    
    # Configuration des seuils
    JOURS_AVANT_ALERTE_RETARD = 0  # Alerte dès le jour de la date de retour prévue
    JOURS_AVANT_RAPPEL = 2  # Nombre de jours avant la date de retour pour envoyer un rappel (info)
    JOURS_AVANT_ALERTE_PERDU = 30  # Matériel considéré perdu après 30 jours
    SEUIL_STOCK_CRITIQUE = 2  # Moins de 2 unités disponibles = stock critique (par nom d'équipement)

    @staticmethod
    def get_attribution_destination_label(attribution):
        """Retourne un libelle de destination lisible pour une attribution."""
        if not attribution:
            return "Sans destination"
        if attribution.client:
            return attribution.client.nom
        if attribution.salle:
            return f"Salle: {attribution.salle.nom}"
        return "Sans destination"

    @staticmethod
    def get_materiel_related_attributions(materiel, limit=None):
        """Retourne les attributions d'un materiel, actives d'abord puis recentes."""
        if not materiel:
            return []

        queryset = Attribution.objects.filter(materiel=materiel).select_related(
            'client', 'salle', 'departement', 'employe_responsable', 'materiel'
        ).order_by(
            Case(
                When(date_retour_effective__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            '-date_attribution'
        )

        if limit:
            queryset = queryset[:limit]

        attributions = list(queryset)
        for attribution in attributions:
            attribution.destination_label = AlerteService.get_attribution_destination_label(attribution)
            attribution.is_active_assignment = attribution.date_retour_effective is None
        return attributions

    @classmethod
    def enrich_alerte_with_attributions(cls, alerte, history_limit=5):
        """Ajoute le contexte d'attribution d'un materiel a une alerte."""
        if not alerte:
            return alerte

        related_attributions = []
        seen_ids = set()

        direct_attribution = getattr(alerte, 'attribution', None) if getattr(alerte, 'attribution_id', None) else None
        if direct_attribution:
            direct_attribution.destination_label = cls.get_attribution_destination_label(direct_attribution)
            direct_attribution.is_active_assignment = direct_attribution.date_retour_effective is None
            related_attributions.append(direct_attribution)
            seen_ids.add(direct_attribution.pk)

        if getattr(alerte, 'materiel_id', None):
            extra_limit = history_limit + (1 if direct_attribution else 0) if history_limit else None
            for attribution in cls.get_materiel_related_attributions(alerte.materiel, limit=extra_limit):
                if attribution.pk in seen_ids:
                    continue
                related_attributions.append(attribution)
                seen_ids.add(attribution.pk)
                if history_limit and len(related_attributions) >= history_limit:
                    break

        attribution_concernee = direct_attribution
        if not attribution_concernee and related_attributions:
            attribution_concernee = next(
                (item for item in related_attributions if item.date_retour_effective is None),
                related_attributions[0],
            )

        alerte.attribution_concernee = attribution_concernee
        alerte.attributions_materiel = related_attributions
        alerte.has_related_attributions = bool(related_attributions)
        alerte.attribution_concernee_is_fallback = bool(
            attribution_concernee and not getattr(alerte, 'attribution_id', None)
        )
        return alerte

    @classmethod
    def enrich_alertes_with_attributions(cls, alertes, history_limit=3):
        """Ajoute un contexte d'attribution a une collection d'alertes."""
        return [cls.enrich_alerte_with_attributions(alerte, history_limit=history_limit) for alerte in alertes]
    
    @staticmethod
    def detecter_retards_retour():
        """Détecte les attributions avec retard de retour"""
        aujourdhui = timezone.now().date()
        attributions_en_retard = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            date_retour_prevue__lt=aujourdhui,
            date_retour_effective__isnull=True
        ).select_related('materiel', 'client', 'departement', 'salle')
        
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
                
                dest_label = attribution.client.nom if attribution.client else (f"Salle: {attribution.salle}" if attribution.salle else 'Inconnu')

                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_RETARD,
                    severite=severite,
                    materiel=attribution.materiel,
                    attribution=attribution,
                    departement=attribution.departement,
                    description=f"Retard de retour: {jours_retard} jour(s) de retard. "
                               f"Date retour prévue: {attribution.date_retour_prevue}. "
                               f"Destinataire: {dest_label}"
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
                attribution_active = next(
                    (item for item in AlerteService.get_materiel_related_attributions(materiel, limit=3) if item.date_retour_effective is None),
                    None,
                )
                attribution_hint = ""
                if attribution_active:
                    attribution_hint = (
                        f" Attribution en cours: {AlerteService.get_attribution_destination_label(attribution_active)}"
                        f" depuis le {attribution_active.date_attribution:%d/%m/%Y %H:%M}."
                    )
                # Pour coller a la regle metier: materiel defectueux doit etre traite
                # comme critique (ex: panne/defaut necessitant action immediate).
                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_DEFECTUEUX,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=materiel,
                    attribution=attribution_active,
                    departement=materiel.departement,
                    description=f"Materiel defectueux necessitant intervention: {materiel.nom} "
                               f"({materiel.asset_id}). Statut: {materiel.get_statut_disponibilite_display()}."
                               f"{attribution_hint}"
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
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            date_retour_prevue__lt=date_limite,
            date_retour_effective__isnull=True
        ).select_related('materiel', 'client', 'departement', 'salle')
        
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
                dest_label = attribution.client.nom if attribution.client else (f"Salle: {attribution.salle}" if attribution.salle else 'Inconnu')

                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_PERDU,
                    severite=Alerte.SEVERITE_CRITICAL,
                    materiel=attribution.materiel,
                    attribution=attribution,
                    departement=attribution.departement,
                    description=f"Matériel considéré comme perdu: {attribution.materiel.nom} "
                               f"({attribution.materiel.asset_id}). "
                               f"Non retourné depuis {jours_ecoules} jour(s). "
                               f"Destinataire: {dest_label}. "
                               f"Date retour prévue: {attribution.date_retour_prevue}"
                )
                alertes_creees.append(alerte)
        
        return alertes_creees

    @staticmethod
    def detecter_rappels_retour():
        """Détecte les attributions dont la date de retour prévue approche et crée des rappels (INFO).

        Créera une alerte de type RETARD mais de sévérité INFO pour indiquer un rappel avant la date de retour.
        """
        aujourdhui = timezone.now().date()
        date_limite = aujourdhui + timedelta(days=AlerteService.JOURS_AVANT_RAPPEL)

        attributions_a_reminder = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            date_retour_prevue__gte=aujourdhui,
            date_retour_prevue__lte=date_limite,
            date_retour_effective__isnull=True
        ).select_related('materiel', 'client', 'departement', 'salle')

        alertes_creees = []
        for attribution in attributions_a_reminder:
            # Ne pas dupliquer un rappel déjà créé
            alerte_existante = Alerte.objects.filter(
                type_alerte=Alerte.TYPE_RETARD,
                attribution=attribution,
                severite=Alerte.SEVERITE_INFO,
                reglementee=False
            ).first()

            if not alerte_existante:
                jours_restants = (attribution.date_retour_prevue - aujourdhui).days
                dest_label = attribution.client.nom if attribution.client else (f"Salle: {attribution.salle}" if attribution.salle else 'Inconnu')

                alerte = Alerte.objects.create(
                    type_alerte=Alerte.TYPE_RETARD,
                    severite=Alerte.SEVERITE_INFO,
                    materiel=attribution.materiel,
                    attribution=attribution,
                    departement=attribution.departement,
                    description=f"Rappel: date de retour prévue dans {jours_restants} jour(s) ({attribution.date_retour_prevue}). "
                                f"Destinataire: {dest_label}"
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
            'rappels': cls.detecter_rappels_retour(),
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
            'materiel', 'attribution__client', 'attribution__salle',
            'attribution__employe_responsable', 'attribution__departement', 'departement'
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

