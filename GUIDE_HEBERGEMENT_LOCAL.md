# 🏢 Guide d'Hébergement Local - RadGestMat

## 📋 Vue d'Ensemble

Ce guide explique comment héberger RadGestMat sur un PC Windows dans le réseau admin de l'hôtel, permettant l'accès depuis les autres départements via Ethernet (réseau admin câblé uniquement).

### Architecture Réseau

```
┌─────────────────────────────────────┐
│  Réseau Admin (Ethernet Câblé)      │
│  IP Fixe: 10.105.42.118              │
│  ┌──────────┐  ┌──────────┐         │
│  │ PC Serveur│  │ PC Users │         │
│  │ (Ethernet)│  │(Ethernet)│         │
│  └────┬─────┘  └──────────┘         │
│       │                              │
│  ┌────▼─────┐                        │
│  │ RadGestMat│                       │
│  │ :8000     │                       │
│  └──────────┘                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  WiFi Client (HostHospitality)      │
│  (Séparé - pas d'accès au réseau)   │
│  ❌ Smartphones ne peuvent pas       │
│     accéder à l'application         │
└─────────────────────────────────────┘
```

**Important** : 
- Le réseau admin est **uniquement Ethernet (câblé)**, il n'y a **pas de WiFi admin**
- Le WiFi client (HostHospitality) est séparé et ne peut **pas** accéder au réseau admin
- Seuls les **PC connectés en Ethernet** au réseau admin peuvent accéder à l'application
- Les **smartphones ne peuvent pas accéder** (pas de WiFi admin disponible)
- **IP fixe du serveur** : `10.105.42.118`

---

## 🚀 Démarrage Rapide (Administrateur)

### Prérequis

- Windows 10/11 ou Windows Server
- Python 3.11+ installé
- Environnement virtuel Python configuré
- Droits administrateur (pour configurer le firewall)

### Étapes

1. **Ouvrir PowerShell** (en tant qu'administrateur recommandé)

2. **Naviguer vers le projet**
   ```powershell
   cd S:\Brice\RadGestMat
   ```

3. **Lancer le script de démarrage**
   ```powershell
   .\scripts\start_local_network.ps1
   ```

4. **L'application est accessible** sur `http://10.105.42.118:8000` (IP fixe)

### Exemple de Sortie

```
================================================
  RADGESTMAT - HÉBERGEMENT RÉSEAU LOCAL
================================================

🔍 1. Configuration de l'IP...
   ✅ IP fixe configurée: 10.105.42.118

🔥 2. Configuration du firewall Windows...
   ✅ Règle firewall créée: 'RadGestMat HTTP' (Port 8000)

🐍 3. Vérification de l'environnement Python...
   ✅ Environnement trouvé: env_new

⚙️  4. Configuration des variables d'environnement...
   ✅ Variables configurées

📍 Informations d'accès:
   🌐 Depuis ce PC: http://localhost:8000
   🌐 Depuis autres PC (réseau admin Ethernet): http://10.105.42.118:8000
   ⚠️  Smartphones: Accès impossible (réseau admin uniquement Ethernet)
```

---

## 📱 Accès depuis Autres Appareils

> **📖 Guide Utilisateur Complet** : Pour des instructions détaillées à partager avec les utilisateurs, consultez [`GUIDE_ACCES_UTILISATEURS.md`](GUIDE_ACCES_UTILISATEURS.md)

### Depuis un PC (Réseau Admin)

1. **Obtenir l'IP du serveur**
   - L'IP est affichée au démarrage du serveur
   - Ou demander à l'administrateur

2. **Ouvrir un navigateur**
   - Chrome, Edge, Firefox, etc.

3. **Aller à l'adresse**
   ```
   http://10.105.42.118:8000
   ```
   *(IP fixe du serveur)*

4. **Se connecter**
   - Utiliser vos identifiants Django
   - Si vous n'avez pas de compte, contacter l'administrateur

### ⚠️ Accès Smartphone

**Le réseau admin est uniquement Ethernet (câblé), il n'y a pas de WiFi admin.**

**Les smartphones ne peuvent pas accéder à l'application** car :
- Le réseau admin est uniquement Ethernet (câblé)
- Le WiFi client (HostHospitality) est séparé et ne peut pas accéder au réseau admin
- Il n'existe pas de WiFi admin

**Solution alternative** : Si un accès smartphone est nécessaire, il faudrait :
- Configurer un point d'accès WiFi sur le réseau admin (demander à l'IT)
- Ou utiliser un VPN pour accéder au réseau admin depuis le WiFi client

---

## 🔧 Configuration Avancée

### Scripts Disponibles

#### 1. Détection IP Locale
```powershell
.\scripts\get_local_ip.ps1
.\scripts\get_local_ip.ps1 -Verbose  # Plus de détails
```

#### 2. Configuration Firewall
```powershell
# Créer la règle (nécessite admin)
.\scripts\configure_firewall.ps1

# Supprimer la règle
.\scripts\configure_firewall.ps1 -Remove
```

#### 3. Démarrage avec Options
```powershell
# Ignorer la configuration firewall
.\scripts\start_local_network.ps1 -SkipFirewall

# Mode verbeux
.\scripts\start_local_network.ps1 -Verbose
```

### Variables d'Environnement

Le script configure automatiquement ces variables :

- `LOCAL_NETWORK_IP` : IP locale détectée
- `DJANGO_SETTINGS_MODULE` : `radgestmat.settings.local_network`
- `ALLOWED_HOSTS` : IP locale + localhost
- `CSRF_TRUSTED_ORIGINS` : URLs autorisées pour CSRF
- `QR_DOMAIN` : Domaine pour les QR codes

### Fichier de Configuration

Le fichier `radgestmat/settings/local_network.py` :
- Détecte automatiquement l'IP locale
- Configure ALLOWED_HOSTS dynamiquement
- Utilise SQLite par défaut (pas de Redis requis)
- Cache en mémoire locale
- Sessions en base de données

---

## 🛠️ Dépannage

### Problème : "IP non détectée"

**Symptôme** : Le script affiche `127.0.0.1` ou une erreur

**Solutions** :
1. Vérifier que le PC est connecté au réseau admin
2. Vérifier que l'interface réseau est active
3. Lancer avec `-Verbose` pour plus de détails :
   ```powershell
   .\scripts\get_local_ip.ps1 -Verbose
   ```
4. Vérifier manuellement l'IP :
   ```powershell
   Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'}
   ```

### Problème : "Accès refusé depuis autre PC"

**Symptôme** : Impossible d'accéder depuis un autre PC

**Solutions** :
1. **Vérifier le firewall Windows**
   ```powershell
   Get-NetFirewallRule -DisplayName "RadGestMat HTTP"
   ```
   Si la règle n'existe pas :
   ```powershell
   .\scripts\configure_firewall.ps1
   ```

2. **Vérifier que les PC sont sur le même réseau**
   - Ping depuis l'autre PC : `ping <IP_SERVEUR>`
   - Si le ping échoue, les PC ne sont pas sur le même réseau

3. **Vérifier ALLOWED_HOSTS**
   - L'IP doit être dans ALLOWED_HOSTS
   - Vérifier dans les logs Django au démarrage

4. **Vérifier que Django écoute sur 0.0.0.0**
   - Le serveur doit être lancé avec `0.0.0.0:8000` (pas `127.0.0.1:8000`)
   - Le script le fait automatiquement

### Problème : "Smartphone ne peut pas accéder"

**Symptôme** : Le smartphone ne charge pas la page

**Solutions** :
1. **Vérifier le réseau WiFi**
   - Le smartphone doit être sur le **WiFi admin** (pas le WiFi client)
   - Le WiFi client HostHospitality est séparé et ne peut pas accéder au réseau admin

2. **Vérifier l'IP**
   - Utiliser la même IP que pour les PC
   - Vérifier que l'IP est correcte (peut changer avec DHCP)

3. **Tester depuis un PC d'abord**
   - Si ça marche depuis un PC, le problème vient du réseau du smartphone

### Problème : "L'IP a changé"

**Symptôme** : L'application ne fonctionne plus après un redémarrage ou changement réseau

**Cause** : Le PC est en DHCP et l'IP a changé

**Solutions** :
1. **Court terme** : Redémarrer le script
   ```powershell
   .\scripts\start_local_network.ps1
   ```
   Noter la nouvelle IP et informer les utilisateurs

2. **Moyen terme** : Utiliser le nom d'hôte réseau (si DNS disponible)
   - Configurer un nom d'hôte dans le DNS interne
   - Utiliser `http://nom-serveur:8000` au lieu de l'IP

3. **Long terme** : Configurer une IP fixe ou réservation DHCP
   - Contacter l'IT pour réserver une IP DHCP
   - Ou configurer une IP fixe dans les paramètres réseau Windows

### Problème : "Port 8000 déjà utilisé"

**Symptôme** : Erreur "Address already in use"

**Solutions** :
1. **Trouver le processus qui utilise le port**
   ```powershell
   netstat -ano | findstr :8000
   ```

2. **Arrêter le processus** (remplacer PID par le numéro trouvé)
   ```powershell
   taskkill /PID <PID> /F
   ```

3. **Ou utiliser un autre port**
   - Modifier le script pour utiliser un autre port (ex: 8001)
   - N'oubliez pas de mettre à jour le firewall

### Problème : "Erreur de migration"

**Symptôme** : Erreur lors des migrations Django

**Solutions** :
1. **Appliquer les migrations manuellement**
   ```powershell
   python manage.py migrate
   ```

2. **Vérifier la base de données**
   - Vérifier que `db.sqlite3` existe et n'est pas corrompu
   - Faire une sauvegarde avant toute modification

---

## 🔐 Sécurité

### Configuration Actuelle

- **Firewall Windows** : Port 8000 ouvert uniquement sur réseau local (Domain, Private)
- **Django ALLOWED_HOSTS** : Restrictif (IP locale uniquement)
- **HTTPS** : Non requis (réseau interne)
- **Authentification** : Obligatoire (Django auth)

### Recommandations

1. **Changer le SECRET_KEY** en production
   ```python
   # Dans radgestmat/settings/local_network.py
   SECRET_KEY = os.environ.get('SECRET_KEY', 'votre-secret-key-securise')
   ```

2. **Utiliser des mots de passe forts** pour les comptes admin

3. **Limiter l'accès réseau** si possible (VLAN dédié)

4. **Sauvegardes régulières** de la base de données

---

## 📊 Monitoring

### Vérifier l'État du Serveur

```powershell
# Vérifier que Django tourne
Get-Process python | Where-Object {$_.CommandLine -like "*manage.py*"}

# Vérifier le port
netstat -ano | findstr :8000

# Vérifier les logs
Get-Content logs\radgestmat.log -Tail 50
```

### Logs Django

Les logs sont disponibles dans :
- `logs/radgestmat.log` : Logs généraux
- `logs/errors.log` : Erreurs uniquement
- Console : Logs en temps réel lors du démarrage

---

## 💾 Sauvegardes

### Sauvegarde Manuelle

```powershell
# Créer un dossier de sauvegarde
New-Item -ItemType Directory -Path "backups" -Force

# Sauvegarder la base de données
$date = Get-Date -Format "yyyyMMdd_HHmm"
Copy-Item db.sqlite3 "backups\db_$date.sqlite3"
```

### Sauvegarde Automatique

Créer une tâche planifiée Windows :

1. Ouvrir "Planificateur de tâches"
2. Créer une tâche de base
3. Déclencher : Quotidien à 2h du matin
4. Action : Exécuter le script de sauvegarde

---

## 📞 Support

### Informations à Fournir en Cas de Problème

1. **Version Python** : `python --version`
2. **IP détectée** : Résultat de `.\scripts\get_local_ip.ps1`
3. **Erreurs** : Contenu de `logs/errors.log`
4. **Configuration réseau** : Résultat de `ipconfig /all`
5. **Firewall** : Résultat de `Get-NetFirewallRule -DisplayName "RadGestMat HTTP"`

### Ressources

- Documentation Django : https://docs.djangoproject.com/
- Guide de déploiement Django : https://docs.djangoproject.com/en/stable/howto/deployment/

---

## ✅ Checklist de Déploiement

- [ ] Python 3.11+ installé
- [ ] Environnement virtuel créé et dépendances installées
- [ ] Base de données initialisée (`python manage.py migrate`)
- [ ] Superutilisateur créé (`python manage.py createsuperuser`)
- [ ] Script de démarrage testé
- [ ] IP détectée correctement
- [ ] Firewall configuré
- [ ] Accès testé depuis un autre PC
- [ ] Accès testé depuis un smartphone (si applicable)
- [ ] Utilisateurs informés de l'URL d'accès
- [ ] Sauvegardes configurées

---

## 🎯 Résumé

**Pour démarrer** :
```powershell
.\scripts\start_local_network.ps1
```

**URL d'accès** : `http://10.105.42.118:8000` (IP fixe)

**Important** : 
- Accès uniquement depuis **PC connectés en Ethernet** au réseau admin
- Les **smartphones ne peuvent pas accéder** (pas de WiFi admin)
- IP fixe : `10.105.42.118` (ne change pas)
- Le firewall doit être configuré (fait automatiquement si admin)

---

**Dernière mise à jour** : Décembre 2025  
**Version** : 1.0.0
