from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.core.files.base import ContentFile
import io
import os
try:
    import qrcode
except ImportError:
    qrcode = None


class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='categories')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = ('nom', 'departement')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.departement.code})"


class Materiel(models.Model):
    ETAT_FONCTIONNEL = 'FONCTIONNEL'
    ETAT_DEFECTUEUX = 'DEFECTUEUX'
    ETAT_EN_MAINTENANCE = 'EN_MAINTENANCE'
    ETAT_CHOICES = [(ETAT_FONCTIONNEL, 'Fonctionnel'), (ETAT_DEFECTUEUX, 'Défectueux'), (ETAT_EN_MAINTENANCE, 'En maintenance')]
    
    STATUT_DISPONIBLE = 'DISPONIBLE'
    STATUT_ATTRIBUE = 'ATTRIBUE'
    STATUT_MAINTENANCE = 'MAINTENANCE'
    STATUT_HORS_SERVICE = 'HORS_SERVICE'
    STATUT_CHOICES = [(STATUT_DISPONIBLE, 'Disponible'), (STATUT_ATTRIBUE, 'Attribué'), (STATUT_MAINTENANCE, 'Maintenance'), (STATUT_HORS_SERVICE, 'Hors service')]
    
    asset_id = models.CharField(max_length=50, default='NEW')
    numero_inventaire = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='materiels')
    marque = models.CharField(max_length=100, blank=True, null=True)
    modele = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    etat_technique = models.CharField(max_length=20, choices=ETAT_CHOICES, default=ETAT_FONCTIONNEL)
    statut_disponibilite = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_DISPONIBLE)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='materiels')
    date_achat = models.DateField(blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    qr_code = models.FileField(upload_to='qr_codes/', blank=True, null=True)
    # Salle de conférence à laquelle le matériel peut être assigné (optionnel)
    salle = models.ForeignKey('Salle', on_delete=models.SET_NULL, null=True, blank=True, related_name='materiels')
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    

    class Meta:
        verbose_name = "Matériel"
        verbose_name_plural = "Matériels"
        unique_together = ('asset_id', 'departement')
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.asset_id} - {self.nom}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Validation explicite : le département est requis avant génération du QR code
            if not self.departement_id:
                raise ValidationError("Le département est requis pour créer un matériel.")
            try:
                import qrcode as qr_module
                domain = os.environ.get('QR_DOMAIN', 'http://localhost:8000')
                checkin_url = f"{domain}/materiel/{self.asset_id}/checkin/"
                qr = qr_module.QRCode(version=1, box_size=10, border=5)
                qr.add_data(checkin_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_io = io.BytesIO()
                img.save(qr_io, format='PNG')
                qr_io.seek(0)
                filename = f"qr_{self.departement.code}_{self.asset_id}.png"
                self.qr_code = ContentFile(qr_io.read(), name=filename)
            except Exception as e:
                print(f"Erreur génération QR: {e}")
        super().save(*args, **kwargs)


class Client(models.Model):
    TYPE_HEBERGEMENT, TYPE_CONFERENCE, TYPE_INTERNE = 'HEBERGEMENT', 'CONFERENCE', 'INTERNE'
    # NOTE: Nous conservons la valeur technique 'CONFERENCE' pour compatibilité,
    # mais les salles de conférence sont désormais un modèle séparé (`Salle`).
    TYPE_CHOICES = [(TYPE_HEBERGEMENT, 'Hébergement'), (TYPE_CONFERENCE, 'Client externe'), (TYPE_INTERNE, 'Interne')]
    
    nom = models.CharField(max_length=200)
    type_client = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_HEBERGEMENT)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    numero_chambre = models.CharField(max_length=20, blank=True, null=True)
    nom_evenement = models.CharField(max_length=200, blank=True, null=True)
    date_arrivee = models.DateField(blank=True, null=True)
    date_depart = models.DateField(blank=True, null=True)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, null=True, blank=True, related_name='clients')
    # Salle associée au client (utile pour les clients externes)
    salle = models.ForeignKey('Salle', on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} ({self.get_type_client_display()})"

    def clean(self):
        # Validation serveur : si le client est de type 'CONFERENCE' (client externe),
        # la salle doit être renseignée.
        if self.type_client == self.TYPE_CONFERENCE and not self.salle:
            raise ValidationError({'salle': 'La salle est requise pour un client externe.'})


class Salle(models.Model):
    """Modèle représentant une salle / lieu (salles de conférence, salle de formation, etc.).

    Nous utilisons ce modèle pour pouvoir attribuer des matériels à une salle.
    """
    nom = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True, related_name='salles')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Salle"
        verbose_name_plural = "Salles"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Attribution(models.Model):
    # Constantes pour durée d'emprunt
    DUREE_COURT_TERME = 'COURT'    # 0-4h
    DUREE_MOYEN_TERME = 'MOYEN'    # 4h-24h
    DUREE_LONG_TERME = 'LONG'      # >24h
    DUREE_CHOICES = [
        (DUREE_COURT_TERME, 'Court terme (< 4h)'),
        (DUREE_MOYEN_TERME, 'Moyen terme (4h - 24h)'),
        (DUREE_LONG_TERME, 'Long terme (> 24h)'),
    ]
    
    # Champs existants
    materiel = models.ForeignKey(Materiel, on_delete=models.CASCADE, related_name='attributions')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attributions', null=True, blank=True)
    employe_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attributions_creees')
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='attributions')
    date_attribution = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    date_retour_effective = models.DateField(blank=True, null=True)
    motif = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    # Optionnel: attribution vers une salle de conférence au lieu d'un client
    salle = models.ForeignKey('Salle', on_delete=models.CASCADE, null=True, blank=True, related_name='attributions')
    
    # Nouveaux champs pour gestion durée d'emprunt
    duree_emprunt = models.CharField(
        max_length=10,
        choices=DUREE_CHOICES,
        default=DUREE_LONG_TERME,
        help_text="Catégorie automatique basée sur la durée totale"
    )
    heure_retour_prevue = models.TimeField(
        null=True,
        blank=True,
        help_text="Heure de retour prévue (pour emprunts < 24h)"
    )
    heure_retour_effective = models.TimeField(
        null=True,
        blank=True,
        help_text="Heure effective de retour"
    )

    class Meta:
        verbose_name = "Attribution"
        verbose_name_plural = "Attributions"
        ordering = ['-date_attribution']
        indexes = [
            models.Index(fields=['duree_emprunt', 'date_retour_effective']),
            models.Index(fields=['date_retour_prevue', 'duree_emprunt']),
        ]

    def __str__(self):
        # Destination may be a client or a salle (or missing). Build a safe label.
        materiel_id = self.materiel.asset_id if self.materiel else '???'
        if self.client:
            dest = self.client.nom
        elif self.salle:
            dest = f"Salle: {self.salle.nom}"
        else:
            dest = "Inconnu"
        return f"{materiel_id}  {dest}"

    def calculate_duree_emprunt(self):
        """Calcul automatique de la catégorie de durée d'emprunt"""
        from django.utils import timezone
        from datetime import datetime, time
        
        if not self.date_retour_prevue:
            return self.DUREE_LONG_TERME
        
        # Conversion en datetime pour calcul précis
        if isinstance(self.date_attribution, datetime):
            start = self.date_attribution
        else:
            start_naive = datetime.combine(self.date_attribution.date() if hasattr(self.date_attribution, 'date') else self.date_attribution, time.min)
            start = timezone.make_aware(start_naive) if timezone.is_naive(start_naive) else start_naive
        
        if self.heure_retour_prevue:
            end_naive = datetime.combine(self.date_retour_prevue, self.heure_retour_prevue)
        else:
            end_naive = datetime.combine(self.date_retour_prevue, time.min)
        
        end = timezone.make_aware(end_naive) if timezone.is_naive(end_naive) else end_naive
        
        delta = end - start
        hours = delta.total_seconds() / 3600
        
        if hours <= 4:
            return self.DUREE_COURT_TERME
        elif hours <= 24:
            return self.DUREE_MOYEN_TERME
        else:
            return self.DUREE_LONG_TERME
    
    def is_overdue(self):
        """Vérifier si l'attribution est en retard"""
        if self.date_retour_effective:
            return False
        
        from django.utils import timezone
        from datetime import datetime, time
        
        today = timezone.now().date()
        
        if self.duree_emprunt in [self.DUREE_COURT_TERME, self.DUREE_MOYEN_TERME]:
            # Pour court/moyen terme: vérifier à partir de l'heure
            if self.heure_retour_prevue:
                retour_datetime = datetime.combine(self.date_retour_prevue, self.heure_retour_prevue)
                return timezone.now() > retour_datetime
        else:
            # Pour long terme: vérifier la date
            return today > self.date_retour_prevue
        
        return False
    
    def get_retard_minutes(self):
        """Retourner le nombre de minutes de retard"""
        if self.date_retour_effective or not self.is_overdue():
            return 0
        
        from django.utils import timezone
        from datetime import datetime, time
        
        if self.heure_retour_prevue:
            retour_datetime = datetime.combine(self.date_retour_prevue, self.heure_retour_prevue)
        else:
            retour_datetime = datetime.combine(self.date_retour_prevue, time(10, 0))
        
        delta = timezone.now() - retour_datetime
        return int(delta.total_seconds() / 60)

    def save(self, *args, **kwargs):
        # Auto-calculer la durée d'emprunt
        self.duree_emprunt = self.calculate_duree_emprunt()
        
        if not self.pk:
            self.materiel.statut_disponibilite = Materiel.STATUT_ATTRIBUE
            self.materiel.save()
        super().save(*args, **kwargs)


class HistoriqueAttribution(models.Model):
    ACTION_CHECK_OUT, ACTION_CHECK_IN, ACTION_MAINTENANCE, ACTION_MODIFICATION = 'CHECK_OUT', 'CHECK_IN', 'MAINTENANCE', 'MODIFICATION'
    ACTION_CHOICES = [(ACTION_CHECK_OUT, 'Check-out'), (ACTION_CHECK_IN, 'Check-in'), (ACTION_MAINTENANCE, 'Maintenance'), (ACTION_MODIFICATION, 'Modification')]
    
    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE, related_name='historiques')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='historiques_actions')
    etat_avant = models.CharField(max_length=50, blank=True, null=True)
    etat_apres = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique Attribution"
        verbose_name_plural = "Historiques Attribution"
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.get_action_display()} - {self.attribution}"


class Alerte(models.Model):
    TYPE_RETARD, TYPE_DEFECTUEUX, TYPE_STOCK_CRITIQUE, TYPE_PERDU = 'RETARD', 'DEFECTUEUX', 'STOCK_CRITIQUE', 'PERDU'
    TYPE_CHOICES = [(TYPE_RETARD, 'Retard de retour'), (TYPE_DEFECTUEUX, 'Matériel défectueux'), (TYPE_STOCK_CRITIQUE, 'Stock critique'), (TYPE_PERDU, 'Matériel perdu')]
    
    SEVERITE_INFO, SEVERITE_WARNING, SEVERITE_CRITICAL = 'INFO', 'WARNING', 'CRITICAL'
    SEVERITE_CHOICES = [(SEVERITE_INFO, 'Information'), (SEVERITE_WARNING, 'Avertissement'), (SEVERITE_CRITICAL, 'Critique')]
    
    type_alerte = models.CharField(max_length=20, choices=TYPE_CHOICES)
    severite = models.CharField(max_length=20, choices=SEVERITE_CHOICES, default=SEVERITE_WARNING)
    materiel = models.ForeignKey(Materiel, on_delete=models.CASCADE, null=True, blank=True, related_name='alertes')
    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE, null=True, blank=True, related_name='alertes')
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='alertes')
    description = models.TextField()
    reglementee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-date_creation']

    def __str__(self):
        return f"[{self.get_severite_display()}] {self.get_type_alerte_display()}"


class AuditLog(models.Model):
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, blank=True, null=True)
    object_repr = models.CharField(max_length=255, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True, help_text='Diff of changed fields (old->new)')
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, help_text='Optional metadata')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapport (Audit)'
        verbose_name_plural = 'Rapports (Audit)'
        ordering = ['-timestamp']

    def __str__(self):
        user = self.user.username if self.user else 'System'
        ct = f"{self.content_type.app_label}.{self.content_type.model}" if self.content_type else 'Unknown'
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user} {self.action} {ct} ({self.object_repr or self.object_id})"


# ============================================================================
# MODÈLES DE NOTIFICATIONS
# ============================================================================

class NotificationLog(models.Model):
    """Historique et audit des notifications envoyées"""
    
    # Types de notifications
    TYPE_CREATION = 'CREATION'
    TYPE_RAPPEL_2H = 'RAPPEL_2H'
    TYPE_RAPPEL_J_MOINS_2 = 'RAPPEL_J_MOINS_2'
    TYPE_RAPPEL_J_MOINS_1 = 'RAPPEL_J_MOINS_1'
    TYPE_RAPPEL_FINAL = 'RAPPEL_FINAL'
    TYPE_RETARD = 'RETARD'
    TYPE_RESTITUTION = 'RESTITUTION'
    TYPE_CHOICES = [
        (TYPE_CREATION, 'Notification de création'),
        (TYPE_RAPPEL_2H, 'Rappel 2h avant'),
        (TYPE_RAPPEL_J_MOINS_2, 'Rappel J-2'),
        (TYPE_RAPPEL_J_MOINS_1, 'Rappel J-1'),
        (TYPE_RAPPEL_FINAL, 'Rappel jour retour'),
        (TYPE_RETARD, 'Alerte retard'),
        (TYPE_RESTITUTION, 'Confirmation restitution'),
    ]
    
    # Canaux de communication
    CANAL_EMAIL = 'EMAIL'
    CANAL_WHATSAPP = 'WHATSAPP'
    CANAL_CHOICES = [
        (CANAL_EMAIL, 'Email'),
        (CANAL_WHATSAPP, 'WhatsApp'),
    ]
    
    # États de la notification
    STATUT_ENVOYEE = 'ENVOYEE'
    STATUT_ECHEC = 'ECHEC'
    STATUT_ECHEC_PERMANENT = 'ECHEC_PERM'
    STATUT_CHOICES = [
        (STATUT_ENVOYEE, 'Envoyée'),
        (STATUT_ECHEC, 'Échec (retry en cours)'),
        (STATUT_ECHEC_PERMANENT, 'Échec définitif'),
    ]
    
    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    duree_emprunt = models.CharField(max_length=10, help_text="Snapshot de la durée au moment de l'envoi")
    destinataire = models.CharField(max_length=200, help_text="Email ou téléphone du destinataire")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_ENVOYEE)
    message_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID du message provider (Twilio, etc.)")
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_scheduled = models.DateTimeField(null=True, blank=True, help_text="Quand était prévu l'envoi")
    date_tentative_prochaine = models.DateTimeField(null=True, blank=True, help_text="Prochaine tentative de retry")
    erreur_message = models.TextField(blank=True, null=True)
    nb_tentatives = models.IntegerField(default=1)
    
    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['attribution', 'type_notification']),
            models.Index(fields=['statut', 'date_tentative_prochaine']),
            models.Index(fields=['date_envoi']),
        ]
    
    def __str__(self):
        return f"[{self.get_type_notification_display()}] {self.destinataire} - {self.get_statut_display()}"


class NotificationPreferences(models.Model):
    """Préférences de notifications par utilisateur/client"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences', null=True, blank=True)
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='notification_preferences', null=True, blank=True)
    
    # Canaux préférés
    notifications_email = models.BooleanField(default=True, help_text="Recevoir les notifications par email")
    notifications_whatsapp = models.BooleanField(default=False, help_text="Recevoir les notifications par WhatsApp")
    
    # Rappels (long terme)
    rappel_j_moins_2 = models.BooleanField(default=True, help_text="Rappel J-2")
    rappel_j_moins_1 = models.BooleanField(default=True, help_text="Rappel J-1")
    rappel_final = models.BooleanField(default=True, help_text="Rappel jour de retour")
    
    # Rappels (moyen terme)
    rappel_2h_avant = models.BooleanField(default=True, help_text="Rappel 2h avant pour moyen terme")
    
    # Contact WhatsApp (optionnel)
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Numéro WhatsApp (+33612345678)")
    
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Préferences Notification"
        verbose_name_plural = "Préferences Notifications"
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} (User)"
        elif self.client:
            return f"{self.client.nom} (Client)"
        return "Préférences"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Assurer qu'au moins un destinataire (user ou client) est défini
        if not self.user and not self.client:
            raise ValidationError("Soit un utilisateur, soit un client doit être défini")
        # Vérifier le format du téléphone si WhatsApp est activé
        if self.notifications_whatsapp and not self.phone_number:
            raise ValidationError("Un numéro de téléphone est requis pour les notifications WhatsApp")


class WhatsAppConfig(models.Model):
    """Configuration API WhatsApp (Twilio)"""
    
    PROVIDER_TWILIO = 'TWILIO'
    PROVIDER_CHOICES = [
        (PROVIDER_TWILIO, 'Twilio'),
    ]
    
    api_provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_TWILIO,
        help_text="Fournisseur API pour WhatsApp"
    )
    api_key = models.CharField(max_length=255, help_text="Clé API (compte, SID, token, etc.)")
    api_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Secret API (token d'authentification)")
    phone_number_sender = models.CharField(max_length=20, help_text="Numéro Twilio sender (+1234567890 ou lien sandbox)")
    is_active = models.BooleanField(default=False, help_text="Configuration active")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration WhatsApp"
        verbose_name_plural = "Configuration WhatsApp"
    
    def __str__(self):
        return f"{self.get_api_provider_display()} - {self.phone_number_sender} ({'Active' if self.is_active else 'Inactive'})"
