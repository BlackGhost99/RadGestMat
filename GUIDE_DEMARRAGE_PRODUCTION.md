# 🚀 Guide de Démarrage Production - RadGestMat

## Pour Déployer en Production sur le Serveur Local

### **Option 1 : Démarrage Rapide (Test)**

```powershell
# Dans le dossier RadGestMat\RadGestMat
.\scripts\start_production.ps1
```

**Accès :**
- Depuis PC : `http://192.168.1.X:8000` (remplacer X par votre IP)
- Depuis Smartphone : `http://192.168.1.X:8000` (WiFi entreprise)

---

### **Option 2 : Déploiement Complet avec Service Windows**

#### **1. Télécharger NSSM** (Service Manager)
- Aller sur : https://nssm.cc/download
- Télécharger nssm 2.24
- Extraire dans `C:\nssm\`

#### **2. Lancer le Script de Déploiement**

```powershell
# En tant qu'Administrateur
cd C:\Users\BlackGhost\Desktop\RadGestMat\RadGestMat
.\scripts\deploy_production_windows.ps1 -ServerIP "192.168.1.100"
```

Remplacer `192.168.1.100` par l'IP réelle de votre serveur.

#### **3. Configurer l'IP Fixe**

1. `Paramètres Windows` > `Réseau et Internet` > `Ethernet`
2. `Modifier les options de l'adaptateur`
3. Clic droit sur votre connexion > `Propriétés`
4. `Protocole Internet version 4 (TCP/IPv4)` > `Propriétés`
5. Cocher `Utiliser l'adresse IP suivante`
6. Saisir :
   - **IP** : `192.168.1.100` (ou autre adresse libre)
   - **Masque** : `255.255.255.0`
   - **Passerelle** : `192.168.1.1` (IP de votre routeur)
   - **DNS** : `8.8.8.8`

#### **4. Gérer le Service**

```powershell
# Démarrer
nssm start RadGestMat

# Arrêter
nssm stop RadGestMat

# Redémarrer
nssm restart RadGestMat

# Statut
nssm status RadGestMat

# Logs
nssm get RadGestMat AppStdout
```

---

## 📱 Accès depuis Smartphone

### **Configuration**

1. Connecter le smartphone au **WiFi de l'entreprise**
2. Ouvrir **Chrome** ou **Safari**
3. Aller sur `http://192.168.1.100:8000` (IP du serveur)
4. Se connecter avec le compte admin

### **Ajouter à l'Écran d'Accueil (comme une app)**

**Sur Android :**
1. Dans Chrome, ouvrir le menu `⋮`
2. `Ajouter à l'écran d'accueil`
3. L'icône RadGestMat apparaît comme une application

**Sur iPhone :**
1. Dans Safari, cliquer sur `Partager` 📤
2. `Sur l'écran d'accueil`
3. L'icône apparaît comme une app native

---

## ⚙️ Configuration Email et WhatsApp

### **1. Éditer `.env.production`**

```powershell
notepad C:\RadGestMat\RadGestMat\.env.production
```

### **2. Configuration Gmail**

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre.email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
```

**Obtenir le mot de passe d'application :**
1. Aller sur https://myaccount.google.com/security
2. `Validation en deux étapes` (activer si nécessaire)
3. `Mots de passe des applications`
4. Sélectionner `Autre` > Saisir "RadGestMat"
5. Copier le mot de passe généré (16 caractères)

### **3. Configuration WhatsApp Twilio**

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

Voir `TEST_WHATSAPP.md` pour les instructions complètes.

---

## 🔒 Sécurité

### **Pare-feu**

Le script de déploiement configure automatiquement :
- Port 8000 (Django)
- Port 80 (HTTP)

### **Utilisateurs**

Créer des comptes utilisateurs via l'admin :
1. `http://192.168.1.100:8000/admin/`
2. `Utilisateurs` > `Ajouter`
3. Assigner un rôle : SUPER_ADMIN, DEPT_MANAGER, GESTIONNAIRE, VIEWER

### **Backups Automatiques**

Configuré pour sauvegarder tous les jours à 2h du matin :
- Emplacement : `C:\RadGestMat\RadGestMat\backups\`
- Rétention : 7 jours

**Backup manuel :**
```powershell
.\scripts\backup_prod.ps1
```

---

## 🔄 Mises à Jour

### **Mettre à jour le code**

```powershell
cd C:\RadGestMat\RadGestMat

# Activer l'environnement
.\env_prod\Scripts\Activate.ps1

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Redémarrer le service
nssm restart RadGestMat
```

---

## 📊 Monitoring

### **Logs Django**

```powershell
# Afficher les logs en temps réel
Get-Content C:\RadGestMat\RadGestMat\logs\radgestmat.log -Tail 100 -Wait

# Afficher les derniers logs
Get-Content C:\RadGestMat\RadGestMat\logs\radgestmat.log -Tail 50
```

### **Logs du Service**

```powershell
# Logs du service Windows
Get-EventLog -LogName Application -Source RadGestMat -Newest 50
```

### **Statistiques Notifications**

1. Aller sur `http://192.168.1.100:8000/notifications/dashboard/`
2. Voir :
   - Total envoyées
   - Taux de succès
   - Répartition Email/WhatsApp
   - Historique complet

---

## 🆘 Dépannage

### **Le serveur ne démarre pas**

```powershell
# Vérifier les logs
Get-Content logs\radgestmat.log -Tail 50

# Vérifier le port
netstat -ano | findstr :8000

# Tester manuellement
.\env_prod\Scripts\python.exe manage.py runserver
```

### **Impossible d'accéder depuis un autre PC**

1. Vérifier le pare-feu :
   ```powershell
   Get-NetFirewallRule -DisplayName "RadGestMat*"
   ```

2. Désactiver temporairement le pare-feu pour tester

3. Vérifier l'IP du serveur :
   ```powershell
   ipconfig
   ```

4. Ping depuis l'autre PC :
   ```cmd
   ping 192.168.1.100
   ```

### **Impossible d'accéder depuis smartphone**

1. Vérifier que le smartphone est sur le **même WiFi**
2. Essayer avec `http://` (pas `https://`)
3. Vérifier l'IP : `ipconfig` sur le serveur
4. Désactiver le VPN sur le smartphone

### **Erreur 500**

```powershell
# Activer DEBUG temporairement pour voir l'erreur
$env:DEBUG = "True"
.\env_prod\Scripts\python.exe manage.py runserver

# Puis redémarrer en production
$env:DEBUG = "False"
```

---

## 📞 Support

- **Documentation complète** : `DEPLOIEMENT_PRODUCTION_INTERNE.md`
- **Logs** : `logs/radgestmat.log`
- **Tests** : `scripts/test_notifications_complete.py`

---

## ✅ Checklist Avant Production

- [ ] IP fixe configurée sur le serveur
- [ ] Service Windows installé et démarré
- [ ] Pare-feu configuré (ports 8000, 80)
- [ ] Email SMTP configuré et testé
- [ ] WhatsApp Twilio configuré (optionnel)
- [ ] Compte admin créé
- [ ] Backup automatique configuré
- [ ] Accès testé depuis PC
- [ ] Accès testé depuis smartphone (WiFi)
- [ ] Dashboard notifications accessible
- [ ] Scheduler démarré (notifications auto)

**Une fois tout validé, RadGestMat est prêt pour la production ! 🎉**
