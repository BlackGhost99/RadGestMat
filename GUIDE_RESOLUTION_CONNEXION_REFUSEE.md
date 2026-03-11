# 🔧 Résolution : ERR_CONNECTION_REFUSED

## Problème

L'erreur "ERR_CONNECTION_REFUSED" apparaît quand vous essayez d'accéder à `http://10.105.42.118:8000` depuis un autre PC.

## Diagnostic Effectué

✅ **Serveur Django** : Démarré et fonctionne (écoute sur 0.0.0.0:8000)  
✅ **IP Configurée** : 10.105.42.118 est présente sur l'interface Ethernet  
✅ **Connexion locale** : Fonctionne depuis le même PC (http://localhost:8000)  
✅ **Connexion IP locale** : Fonctionne depuis le même PC (http://10.105.42.118:8000)  
⚠️ **Firewall** : Règle existe mais peut bloquer les connexions depuis d'autres PC

## Solution

### Étape 1 : Configurer le Firewall Windows

**IMPORTANT** : Vous devez exécuter PowerShell **en tant qu'administrateur**.

1. Clic droit sur PowerShell
2. Sélectionner "Exécuter en tant qu'administrateur"
3. Exécuter :

```powershell
cd S:\Brice\RadGestMat
.\scripts\fix_firewall.ps1
```

Ce script va :
- Supprimer les anciennes règles firewall
- Créer une nouvelle règle qui autorise les connexions entrantes sur le port 8000
- Configurer la règle pour tous les profils réseau (Domain, Private, Public)

### Étape 2 : Vérifier que le serveur est démarré

Le serveur Django doit être en cours d'exécution. Pour le démarrer :

```powershell
cd S:\Brice\RadGestMat
$env:LOCAL_NETWORK_IP = "10.105.42.118"
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.local_network"
$env:ALLOWED_HOSTS = "10.105.42.118,localhost,127.0.0.1"
python manage.py runserver 0.0.0.0:8000
```

Ou utiliser le script simplifié :

```powershell
.\scripts\start_simple.ps1
```

### Étape 3 : Tester depuis un autre PC

1. Sur un autre PC du réseau admin (Ethernet)
2. Ouvrir un navigateur
3. Aller à : `http://10.105.42.118:8000`
4. La page devrait se charger

## Vérifications

### Vérifier que le serveur écoute

```powershell
netstat -ano | findstr :8000
```

Vous devriez voir :
```
TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING
```

### Vérifier la règle firewall

```powershell
Get-NetFirewallRule -DisplayName "RadGestMat HTTP" | Select-Object DisplayName, Enabled, Direction, Action
```

Vous devriez voir :
- DisplayName : RadGestMat HTTP
- Enabled : True
- Direction : Inbound
- Action : Allow

### Tester la connexion depuis le serveur

```powershell
Invoke-WebRequest -Uri "http://10.105.42.118:8000" -UseBasicParsing
```

Devrait retourner : StatusCode 200

## Si le problème persiste

1. **Vérifier que les PC sont sur le même réseau**
   ```powershell
   # Sur le serveur
   ipconfig
   # Notez l'adresse IP et le masque de sous-réseau
   
   # Sur le PC client
   ping 10.105.42.118
   # Si le ping fonctionne, les PC sont sur le même réseau
   ```

2. **Vérifier qu'aucun autre firewall ne bloque**
   - Antivirus avec firewall intégré
   - Firewall d'entreprise
   - Routeur avec filtrage

3. **Vérifier les logs Django**
   - Les logs devraient montrer les tentatives de connexion
   - Si aucune tentative n'apparaît, le problème est réseau/firewall
   - Si des erreurs apparaissent, c'est un problème Django

## Script de Démarrage Complet

Pour éviter les problèmes d'encodage avec le script principal, utilisez `start_simple.ps1` :

```powershell
.\scripts\start_simple.ps1
```

Ce script :
- Configure les variables d'environnement
- Trouve Python automatiquement
- Vérifie le port et l'IP
- Démarre le serveur Django

---

**Note** : Le script `start_local_network.ps1` a des problèmes d'encodage PowerShell. Utilisez `start_simple.ps1` en attendant la correction.
