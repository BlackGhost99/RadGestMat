# RadGestMat Android — APK de test

Cette première APK est un conteneur Android WebView de l'interface Django existante, pour permettre un premier test sur téléphone. Elle ne remplace pas encore une application Android native hors ligne.

## Construction

Le workflow GitHub Actions `Android APK (test)` construit `app-debug.apk` sur chaque modification de ce dossier sur `feature/android-offline-app`. L'APK est publié comme artefact GitHub Actions pendant 14 jours.

## Installation

1. Ouvrir l'onglet Actions du dépôt.
2. Ouvrir le workflow **Android APK (test)** et attendre que le job soit vert.
3. Télécharger l'artefact `RadGestMat-Android-debug` et extraire le ZIP.
4. Copier `app-debug.apk` sur le téléphone Android et l'ouvrir. Autoriser l'installation depuis cette source si Android le demande.
5. Au premier lancement, saisir l'URL HTTPS exacte de l'instance RadGestMat, puis se connecter avec un compte existant.

## Limites de cette version

- Connexion Internet requise.
- Pas de cache de données ni de file d'attente hors ligne.
- Pas de nouvelles opérations d'attribution/retour natives.
- La caméra n'est accordée qu'à une page HTTPS qui la demande et après permission Android.
- APK debug destiné aux essais, non à une diffusion publique.
