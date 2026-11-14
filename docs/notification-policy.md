# Politique de notifications RadGestMat — validée

- Relances toutes les 15 minutes après échéance non traitée.
- Sonnerie et vibration Android activées par défaut.
- Consultation ou effacement de la notification ne clôture pas le suivi.
- Arrêt des relances après traitement effectif enregistré côté serveur (retour confirmé ou autre résolution autorisée et tracée).
- Canaux souhaités : Android natif, email, WhatsApp Business.
- Rappels préventifs proposés : J-1, H-1, à échéance.
- Échéances exprimées en date et heure, stockage timezone-aware, affichage local.
- Déduplication par événement, destinataire, canal et créneau ; journal des tentatives et résultats.
- Respect des permissions Android, préférences système et consentements des destinataires. Pas de garantie de livraison à la minute exacte.
- Les relances sonores Android sont prioritaires ; fréquence des envois email/WhatsApp à définir pour éviter le spam et respecter les limites fournisseurs.

## Mise en œuvre à venir
Auditer les modèles et services existants ; moteur d'échéances durable et planificateur serveur ; centre de notifications ; APK et FCM ; intégrations email et WhatsApp officielles ; tests de retour, doublons, permissions et fonctionnement hors connexion.

Ce document fixe les exigences validées ; il ne constitue pas une activation technique des notifications.
