from django.db.models.signals import post_save
from django.dispatch import receiver

# Signal désactivé - Le profil est créé via l'admin inline
# Pour créer un profil utilisateur manuellement en dehors de l'admin:
# from assets.models import Departement
# departement = Departement.objects.first()
# ProfilUtilisateur.objects.create(user=user_instance, departement=departement)

# @receiver(post_save, sender='auth.User', dispatch_uid='create_user_profile_signal')
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     """Crée un profil utilisateur quand un nouvel utilisateur est créé"""
#     pass