# Configuration Microsoft Graph pour RadGestMat

Ce projet est pret a envoyer les mails via Microsoft Graph pour votre tenant Microsoft 365.

Tenant ID:

```text
your-tenant-id
```

## Variables a renseigner dans `.env`

```env
EMAIL_DELIVERY_METHOD=microsoft_graph
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_GRAPH_SENDER=your-sender@your-company.com
MICROSOFT_GRAPH_SAVE_TO_SENT_ITEMS=True
```

## Ce qu'il faut creer dans Microsoft Entra

1. Creer une App Registration dans le tenant `radissonblu.com`.
2. Recuperer:
   - `Application (client) ID` -> `MICROSOFT_CLIENT_ID`
   - `Directory (tenant) ID` -> deja pre-rempli
3. Creer un `Client secret` -> `MICROSOFT_CLIENT_SECRET`
4. Ajouter la permission Microsoft Graph `Mail.Send` en `Application permission`
5. Donner le `Admin consent` pour cette permission

## Expediteur

L'application enverra en tant que:

```text
your-sender@your-company.com
```

Le compte doit exister dans Microsoft 365 et etre autorise a envoyer. Remplacez les valeurs d'exemple par celles de votre organisation.

## Validation

Apres mise a jour de `.env`, recharger Docker:

```powershell
docker compose up -d --build web nginx
```

Puis tester:

```powershell
docker exec radgestmat_web python manage.py shell -c "from assets.mail_transport import send_email; print(send_email(subject='[RadGestMat] Test Graph', message='Test Graph', recipient_list=['recipient@example.com']))"
```
