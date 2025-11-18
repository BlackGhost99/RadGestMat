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
            try:
                import qrcode as qr_module
                # Générer QR code avec URL check-in
                # En production, remplacer localhost par votre domaine
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
                # Utiliser ContentFile pour assigner directement au champ FileField
                self.qr_code = ContentFile(qr_io.read(), name=filename)
            except Exception as e:
                print(f"Erreur génération QR: {e}")
        super().save(*args, **kwargs)


class Client(models.Model):
    TYPE_HEBERGEMENT, TYPE_CONFERENCE, TYPE_INTERNE = 'HEBERGEMENT', 'CONFERENCE', 'INTERNE'
    TYPE_CHOICES = [(TYPE_HEBERGEMENT, 'Hébergement'), (TYPE_CONFERENCE, 'Conférence'), (TYPE_INTERNE, 'Interne')]
    
    nom = models.CharField(max_length=200)
    type_client = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_HEBERGEMENT)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    numero_chambre = models.CharField(max_length=20, blank=True, null=True)
    nom_evenement = models.CharField(max_length=200, blank=True, null=True)
    date_arrivee = models.DateField(blank=True, null=True)
    date_depart = models.DateField(blank=True, null=True)
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, null=True, blank=True, related_name='clients')
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} ({self.get_type_client_display()})"


class Attribution(models.Model):
    materiel = models.ForeignKey(Materiel, on_delete=models.CASCADE, related_name='attributions')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attributions')
    employe_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attributions_creees')
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='attributions')
    date_attribution = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    date_retour_effective = models.DateField(blank=True, null=True)
    motif = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Attribution"
        verbose_name_plural = "Attributions"
        ordering = ['-date_attribution']

    def __str__(self):
        return f"{self.materiel.asset_id}  {self.client.nom}"

    def save(self, *args, **kwargs):
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
