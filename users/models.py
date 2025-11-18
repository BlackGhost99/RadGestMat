# users/models.py
from django.db import models
from django.contrib.auth.models import User

class ProfilUtilisateur(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Administrateur'),
        ('DEPT_MANAGER', 'Manager Département'),
        ('DEPT_USER', 'Utilisateur Département'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    departement = models.ForeignKey(
        'assets.Departement',  # ✅ Référence par nom d'appli
        on_delete=models.CASCADE
    )
    telephone = models.CharField(max_length=20, blank=True)
    date_embauche = models.DateField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEPT_USER')
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil Utilisateur"
        verbose_name_plural = "Profils Utilisateurs"
    
    def __str__(self):
        return f"{self.user.username} - {self.departement.nom} ({self.role})"
    
    def est_super_admin(self):
        return self.role == 'SUPER_ADMIN'
    
    def est_manager_departement(self):
        return self.role in ['SUPER_ADMIN', 'DEPT_MANAGER']