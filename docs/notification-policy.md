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

## Responsabilité individuelle et visibilité départementale
- Le créateur de l'attribution est le responsable initial du suivi. Les rappels sonores et vibrations sont exclusivement destinés à son téléphone authentifié, jamais diffusés à tout le département.
- Les rappels email et WhatsApp sont également personnels par défaut. Le bénéficiaire du prêt n'est pas automatiquement destinataire.
- Enregistrement du responsable et du département de rattachement de l'opération côté serveur ; contrôle des droits côté serveur, y compris API et historique.
- Tous les membres autorisés du même département consultent un historique commun des attributions, échéances, relances, retards, retours et actions, avec auteur et horodatage. Pas de visibilité interdépartementale sans permission explicite.
- Proposition à valider : transfert explicite et audité du suivi à un collègue autorisé, avec révocation des rappels de l'ancien responsable ; retour enregistré par un collègue habilité arrête les relances du responsable.
- Proposition à valider : un seul téléphone principal actif par profil pour les rappels sonores ; gestion du changement de téléphone, révocation des anciens jetons push et de la session lors de la déconnexion.
- Ne pas confondre consultation d'une alerte, résolution du suivi et droits de modification. L'historique reste accessible après résolution.
