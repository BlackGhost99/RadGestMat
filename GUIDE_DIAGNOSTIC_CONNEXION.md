# 🔍 Guide de Diagnostic - Connexion Refusée

## Problème

Les PC sont sur le même réseau (ping fonctionne), mais `http://10.105.42.118:8000` est inaccessible depuis un autre PC.

## Diagnostic Étape par Étape

### Étape 1 : Vérifier depuis le PC Serveur

Sur le PC serveur (10.105.42.118), exécuter :

```powershell
cd S:\Brice\RadGestMat
.\scripts\test_connection.ps1 -ServerIP 10.105.42.118
```

**Résultat attendu** : Tous les tests doivent passer (Ping OK, Port OK, HTTP OK)

### Étape 2 : Vérifier depuis le PC Client

Sur le PC client (autre PC du réseau), exécuter :

```powershell
# Copier le script test_connection.ps1 sur le PC client
# Ou exécuter directement :
Invoke-WebRequest -Uri "http://10.105.42.118:8000" -UseBasicParsing
```

**Si ça fonctionne** : Le problème est résolu !  
**Si ça échoue** : Continuer avec les étapes suivantes

### Étape 3 : Test du Port TCP

Sur le PC client, tester si le port est accessible :

```powershell
$tcpClient = New-Object System.Net.Sockets.TcpClient
try {
    $tcpClient.Connect("10.105.42.118", 8000)
    Write-Host "Port accessible" -ForegroundColor Green
    $tcpClient.Close()
} catch {
    Write-Host "Port NON accessible: $($_.Exception.Message)" -ForegroundColor Red
}
```

**Si le port n'est pas accessible** : Le problème est réseau/firewall  
**Si le port est accessible mais HTTP échoue** : Le problème est Django

### Étape 4 : Vérifier les Firewalls

#### Sur le PC Serveur

```powershell
# Vérifier la règle firewall
Get-NetFirewallRule -DisplayName "RadGestMat HTTP" | Select-Object DisplayName, Enabled, Direction, Action

# Vérifier les profils firewall
Get-NetFirewallProfile | Select-Object Name, Enabled

# Vérifier les règles de blocage
Get-NetFirewallRule | Where-Object { $_.Enabled -eq $true -and $_.Action -eq 'Block' -and $_.Direction -eq 'Inbound' } | Select-Object DisplayName
```

#### Sur le PC Client

Vérifier si le firewall client bloque les connexions sortantes vers le port 8000.

### Étape 5 : Vérifier les Antivirus

Les antivirus peuvent avoir leur propre firewall qui bloque les connexions :

- **Windows Defender** : Vérifier dans "Pare-feu et protection réseau"
- **Autres antivirus** : Vérifier les paramètres de firewall

### Étape 6 : Vérifier les Logs Django

Sur le PC serveur, vérifier si Django reçoit des tentatives de connexion :

```powershell
# Voir les dernières lignes du log
Get-Content "logs\radgestmat.log" -Tail 20

# Chercher les erreurs
Get-Content "logs\errors.log" -Tail 20
```

**Si aucune tentative n'apparaît dans les logs** : Le problème est réseau/firewall (la requête n'atteint pas Django)  
**Si des erreurs apparaissent** : Le problème est Django (ALLOWED_HOSTS, etc.)

### Étape 7 : Test avec Telnet

Sur le PC client, tester avec telnet :

```powershell
# Activer telnet si nécessaire
# Puis tester :
telnet 10.105.42.118 8000
```

**Si telnet se connecte** : Le port est ouvert, le problème est HTTP/Django  
**Si telnet échoue** : Le port est bloqué par un firewall

## Solutions Possibles

### Solution 1 : Firewall Windows

Si le firewall est désactivé mais bloque quand même, réactiver et créer la règle :

```powershell
# En tant qu'administrateur
Enable-NetFirewallProfile -Profile Domain,Private
.\scripts\fix_firewall.ps1
```

### Solution 2 : Antivirus

Désactiver temporairement le firewall de l'antivirus pour tester.

### Solution 3 : Firewall Client

Vérifier que le firewall du PC client n'bloque pas les connexions sortantes.

### Solution 4 : Routeur/Switch

Vérifier avec l'IT si le routeur/switch a des règles de filtrage qui bloquent le port 8000.

### Solution 5 : ALLOWED_HOSTS

Si Django rejette les connexions, vérifier ALLOWED_HOSTS :

```python
# Dans radgestmat/settings/local_network.py
# S'assurer que l'IP est dans ALLOWED_HOSTS
ALLOWED_HOSTS = ['10.105.42.118', 'localhost', '127.0.0.1', '*']  # '*' pour tester
```

**⚠️ ATTENTION** : Utiliser `'*'` uniquement pour tester, pas en production !

## Test Rapide

Pour tester rapidement si c'est un problème firewall, désactiver temporairement tous les firewalls :

```powershell
# En tant qu'administrateur
Disable-NetFirewallProfile -Profile Domain,Private,Public
```

**Si ça fonctionne après** : Le problème est le firewall  
**Si ça ne fonctionne toujours pas** : Le problème est ailleurs (réseau, Django, etc.)

## Informations à Collecter

Pour un diagnostic complet, collecter :

1. **Sur le serveur** :
   - Résultat de `netstat -ano | findstr :8000`
   - Résultat de `Get-NetFirewallRule -DisplayName "RadGestMat HTTP"`
   - Dernières lignes de `logs\radgestmat.log`

2. **Sur le client** :
   - Résultat de `ping 10.105.42.118`
   - Résultat de `telnet 10.105.42.118 8000` (ou test TCP)
   - Message d'erreur exact du navigateur

3. **Réseau** :
   - Adresse IP du PC client
   - Masque de sous-réseau (doit être le même que le serveur)
   - Passerelle par défaut

---

**Prochaine étape** : Exécuter `.\scripts\test_connection.ps1` depuis le PC client pour identifier où exactement la connexion échoue.
