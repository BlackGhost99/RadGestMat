# Phase 5 Implementation: WhatsApp/Twilio Integration

**Status:** ✅ **COMPLETED**  
**Date:** December 10, 2025  
**Components:** 3 new files, 1 modified

---

## Overview

Phase 5 adds **WhatsApp notifications** to the RadGestMat system via Twilio integration. This provides SMS-style notifications to users who prefer messaging over email, with automatic fallback logic and multi-channel support.

### Key Features

- **Twilio Integration**: Uses Twilio WhatsApp Business API
- **Text-Based Templates**: Concise, emoji-rich WhatsApp messages
- **Fallback Logic**: Email if WhatsApp unavailable
- **Phone Validation**: Automatic phone number formatting and validation
- **Error Handling**: Graceful retry logic with configurable attempt limits
- **Audit Trail**: Full notification log for compliance

---

## Architecture

### Communication Channels

```
┌──────────────────────────────────────────────────────┐
│       Multi-Channel Notification System              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Notification Event                                  │
│         │                                            │
│         ├─→ [TYPE] Creation / Reminder / Overdue    │
│         │                                            │
│         ├─→ NotificationLog.canal selection         │
│         │   ├─ CANAL_EMAIL (primary)               │
│         │   └─ CANAL_WHATSAPP (alternate)          │
│         │                                            │
│         ├─→ EMAIL PATH                              │
│         │   ├─ NotificationEmailService.send()     │
│         │   ├─ Render HTML template                 │
│         │   ├─ Send via SMTP                        │
│         │   └─ Update status: ENVOYEE/ECHEC        │
│         │                                            │
│         └─→ WHATSAPP PATH                           │
│             ├─ WhatsAppNotificationService.send()  │
│             ├─ Validate phone number               │
│             ├─ Connect to Twilio API               │
│             ├─ Send text message                    │
│             └─ Update status: ENVOYEE/ECHEC        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Twilio Flow

```
RadGestMat                  Twilio                    Client
    │                          │                        │
    ├─ Create msg ────────────>│                        │
    │  via API                 │                        │
    │                          ├─ Validate ────────────>│
    │                          │  WhatsApp msg          │
    │                          │                        │
    │                          │<─ Message read ────────┤
    │<─ Delivery ──────────────┤                        │
    │  confirmation            │                        │
    │                          │                        │
    ├─ Update log             │                        │
    │  STATUT=ENVOYEE          │                        │
    │                          │                        │
```

---

## File Structure

### 1. **assets/whatsapp_service.py** (NEW - 200 lines)

Core WhatsApp notification service with Twilio integration.

**Key Components:**

```python
class WhatsAppNotificationService:
    """
    Service for sending WhatsApp notifications via Twilio
    """
    
    @classmethod
    def _get_twilio_client(cls):
        """Initialize Twilio client with credentials from settings"""
        # Validates: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
        # Returns: Client object or None if unconfigured
    
    @staticmethod
    def send_notification(notification_log):
        """
        Core method: Send WhatsApp notification
        
        Flow:
        1. Get Twilio client
        2. Get subject and message body
        3. Validate recipient phone
        4. Format with +country code
        5. Send via messages.create()
        6. Update NotificationLog with status
        7. Retry up to 3 times on failure
        8. Mark as ECHEC_PERMANENT after 3 attempts
        """
    
    @staticmethod
    def _get_subject(notification_log) -> str:
        """Map notification type to emoji subject"""
        # Returns: "✅ Emprunt Confirmé" etc
    
    @staticmethod
    def _get_message_body(notification_log) -> str:
        """Select and render template based on type"""
        # Uses WhatsAppTemplates class
        # Passes: attribution, materiel, client, duree_emprunt
    
    # Wrapper methods with same signature as EmailService
    send_creation_notification(attribution, phone_number, client_type)
    send_reminder_notification(attribution, reminder_type, phone_number)
    send_overdue_alert(attribution, phone_number, days_late)
    send_restitution_notification(attribution, phone_number)
```

**Configuration Required:**

```python
# In radgestmat/settings/development.py

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = 'AC...'  # From Twilio console
TWILIO_AUTH_TOKEN = 'auth_token_here'  # From Twilio console
TWILIO_WHATSAPP_FROM = 'whatsapp:+1234567890'  # Your Twilio number
```

**Error Handling:**

```python
# Phone validation
if not recipient_phone.startswith('+'):
    recipient_phone = '+' + recipient_phone

# Detect invalid phone (email address)
if '@' in recipient_phone:
    status = STATUT_ECHEC_PERMANENT
    message = "Invalid recipient phone number"

# Retry logic
nb_tentatives = 0  # Increment on each failure
if nb_tentatives >= 3:
    status = STATUT_ECHEC_PERMANENT
else:
    status = STATUT_ECHEC
```

**Status Tracking:**

```python
STATUT_EN_ATTENTE           # Initial state
STATUT_ENVOYEE              # Successfully sent
STATUT_ECHEC                # Failed, retry later
STATUT_ECHEC_PERMANENT      # Failed 3x, give up
```

### 2. **assets/whatsapp_templates.py** (NEW - 140 lines)

Text message templates for all notification types.

**Template Class:**

```python
class WhatsAppTemplates:
    """Text templates for WhatsApp messages"""
    
    # Static methods, each takes:
    # attribution, materiel, client, duree_emprunt, **kwargs
    
    @staticmethod
    def creation():
        """✅ Emprunt Confirmé"""
        # Greeting
        # Material name, code
        # Return date/time
        # Instructions
        # Support note
    
    @staticmethod
    def rappel_2h():
        """⏰ RAPPEL - 2 heures avant la restitution!"""
        # Greeting
        # Countdown (2 hours)
        # Material details
        # Condition check reminder
        # Location instructions
    
    @staticmethod
    def rappel_j2():
        """📋 RAPPEL - Restitution dans 2 jours"""
        # Greeting
        # Material details
        # Return date
        # Preparation reminder
        # Accessories check
    
    @staticmethod
    def rappel_j1():
        """🚨 RAPPEL URGENT - Restitution DEMAIN!"""
        # URGENT warning
        # Material details
        # Return date/time
        # Action checklist
        # Late consequence warning
    
    @staticmethod
    def rappel_final():
        """🔴 CRITIQUE - RESTITUTION AUJOURD'HUI!"""
        # CRITICAL header
        # Material details
        # Deadline
        # Consequences of delay
        # Urgent action required
    
    @staticmethod
    def retard():
        """⚠️ ALERTE - MATÉRIEL EN RETARD"""
        # Alert header
        # Material details
        # Current situation
        # Immediate action required
        # Contact information
    
    @staticmethod
    def restitution():
        """✨ MATÉRIEL RESTITUÉ - MERCI!"""
        # Success message
        # Material confirmed returned
        # Loan duration summary
        # Thank you
        # Next steps
```

**Message Characteristics:**

```
✅ Emojis for visual hierarchy
🚨 French language (configurable)
📦 Material reference number
🕐 Time/date information
✅ Action checklist (for urgent messages)
⚠️ Escalation indicators
📍 Location guidance
```

**Example Messages:**

```
✨ MATÉRIEL RESTITUÉ - MERCI!

Bonjour Jean!

Votre emprunt a été officiellement clôturé:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
✅ Statut: Restitué avec succès

📊 Détails de l'emprunt:
• Durée: LONG
• Restitué le: 14:30

Merci d'avoir utilisé notre service de gestion des matériels!

📈 Vous pouvez à nouveau faire une demande d'emprunt.
👍 Bon travail!
```

### 3. **scripts/test_whatsapp.py** (NEW - 230 lines)

Complete test framework for WhatsApp integration.

**Test Stages:**

```python
def test_whatsapp_service():
    """
    STAGE 1: Verify Twilio Configuration
    - Check TWILIO_ACCOUNT_SID
    - Check TWILIO_AUTH_TOKEN
    - Check TWILIO_WHATSAPP_FROM
    - Display configuration status
    
    STAGE 2: Test Message Templates
    - Instantiate WhatsAppTemplates
    - Call each template method
    - Verify message generation
    - Check message length
    
    STAGE 3: Create Test Data
    - Create/fetch Departement
    - Create/fetch User
    - Create/fetch Client with phone
    - Create/fetch Category
    - Create/fetch Materiel
    
    STAGE 4: Create Attribution
    - Create 3-hour test loan
    - Associate with test material/client
    
    STAGE 5: Test WhatsApp Notifications
    - Create NotificationLog for TYPE_CREATION
    - Send via WhatsAppNotificationService
    - Verify STATUT_ENVOYEE
    - Repeat for RAPPEL_2H, RETARD, RESTITUTION
    
    STAGE 6: Display Statistics
    - Count total notifications created
    - Count successfully sent
    - Count failures
    - Print summary
    """
```

**Test Data:**

```
Department: TEST (Test Department)
User: whatsapp_test (Test User)
Client: TestClient with phone +33600000000
Material: Test Material for WhatsApp (WHATSAPP-TEST-001)
Attribution: 3-hour test loan
```

**Usage:**

```bash
# Run test script
python scripts/test_whatsapp.py

# Expected output:
# ✓ Twilio credentials configured
# ✓ 7 templates tested
# ✓ Test data created
# ✓ 4 notifications sent
# Statistics: 4 sent, 0 failed
```

### 4. **requirements.txt** (MODIFIED - Already done in Phase 4)

```txt
twilio==9.2.3  # WhatsApp API client
```

---

## Setup & Configuration

### Step 1: Install Twilio SDK

```bash
pip install twilio==9.2.3
```

### Step 2: Create Twilio Account

1. Go to [twilio.com](https://www.twilio.com)
2. Sign up for free trial account
3. Create a WhatsApp Business Profile
4. Get credentials:
   - **Account SID**: From Twilio Console > Settings
   - **Auth Token**: From Twilio Console > Settings
   - **WhatsApp Number**: Format: `whatsapp:+1234567890`

### Step 3: Configure Django Settings

Add to `radgestmat/settings/development.py`:

```python
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'AC...')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'your_token')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+1234567890')
```

Or use `.env` file:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
```

### Step 4: Test Configuration

```bash
# Test script
python scripts/test_whatsapp.py

# Or manual test
python manage.py shell
>>> from assets.whatsapp_service import WhatsAppNotificationService
>>> client = WhatsAppNotificationService._get_twilio_client()
>>> client  # Should return Client object if configured
```

---

## Integration with Email Service

### Parallel Channel Support

```python
# Phase 2: Email only
NotificationEmailService.send_creation_notification(attribution, email)

# Phase 5: Add WhatsApp
WhatsAppNotificationService.send_creation_notification(attribution, phone, 'client')

# Phase 6+: Unified multi-channel
NotificationDispatcher.send(
    attribution,
    channels=['email', 'whatsapp'],  # Send to both
    email_to=client.email,
    phone_to=client.phone
)
```

### Fallback Logic

```python
def send_with_fallback(attribution, phone):
    """Send WhatsApp, fallback to email if fails"""
    
    # Try WhatsApp first
    if WhatsAppNotificationService.send_notification(notification):
        return True
    
    # Fall back to email
    return NotificationEmailService.send_notification(notification)
```

### Dual-Channel Implementation

```python
# In scheduler_jobs.py
def check_long_terme_reminders():
    for attribution in attributions:
        if should_send_reminder(attribution):
            # Email
            _send_reminder_notification(attribution, type, canal=CANAL_EMAIL)
            
            # WhatsApp if phone available
            if attribution.client.phone:
                _send_reminder_notification(attribution, type, canal=CANAL_WHATSAPP)
```

---

## Message Templates Details

### Creation Message

```
✅ Emprunt Confirmé

Bonjour Jean!

Votre demande d'emprunt a été confirmée:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
📅 Date retour: 2025-12-10
🕐 Heure retour: À convenir

✅ Vous pouvez retirer le matériel au point de distribution.

Pour toute question, contactez-nous!
```

**Audience:** User/client confirming their loan request  
**Context:** Right after attribution creation  
**Action:** Retrieve material from distribution point

### 2-Hour Reminder

```
⏰ RAPPEL - 2 heures avant la restitution!

Bonjour Jean,

Vous devez restituer le matériel suivant dans 2 heures:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
🕐 Heure limite: 16:30

⚠️ Vérifiez que le matériel est en bon état avant la restitution.

📍 Apportez le matériel au point de retour.
```

**Audience:** User 2 hours before return deadline  
**Context:** For short/medium term loans (< 24h)  
**Action:** Prepare for return, quality check

### J-2 Reminder (2 days before)

```
📋 RAPPEL - Restitution dans 2 jours

Bonjour Jean,

Vous avez emprunté un matériel qui doit être restitué dans 2 jours:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
📅 Date retour: 2025-12-12
🕐 Heure retour: Avant 18h

Préparez le matériel et vérifiez son état.

✅ Tous les accessoires doivent être inclus.
```

**Audience:** User 2 days before return  
**Context:** Long-term loans only  
**Action:** Prepare material for return

### J-1 Reminder (1 day before)

```
🚨 RAPPEL URGENT - Restitution DEMAIN!

Bonjour Jean,

Votre emprunt expire DEMAIN:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
📅 Date retour: 2025-12-11
🕐 Heure limite: Avant 18h

⚠️ Actions requises:
• Arrêtez l'utilisation du matériel
• Nettoyez le matériel
• Vérifiez tous les accessoires

❌ Le dépassement peut entraîner des frais de retard.
```

**Audience:** User day before return  
**Context:** Last chance reminder, long-term  
**Action:** Stop using, prepare, prevent delay

### Final Reminder (Day of return)

```
🔴 CRITIQUE - RESTITUTION AUJOURD'HUI!

URGENT Jean!

Le matériel DOIT être restitué AUJOURD'HUI:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
⏰ Heure limite: Avant 18h

🚨 CONSÉQUENCES du dépassement:
• Frais de retard applicables
• Pénalités de non-restitution
• Restriction d'emprunt futur

✅ Apportez le matériel AU PLUS TÔT au point de retour.
```

**Audience:** User on return day  
**Context:** Last day reminder, critical  
**Action:** Return immediately

### Overdue Alert

```
⚠️ ALERTE - MATÉRIEL EN RETARD

Jean,

Le matériel suivant est EN RETARD:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
📅 Date retour prévue: 2025-12-10

🚨 Situation actuelle:
• Matériel non restitué
• Retard en cours
• Frais appliqués

✅ Action immédiate requise:
Restituez le matériel dès que possible!

Pour tout problème, contactez-nous immédiatement.
```

**Audience:** User when overdue  
**Context:** Escalation, regulatory  
**Action:** Return immediately or contact support

### Restitution Confirmation

```
✨ MATÉRIEL RESTITUÉ - MERCI!

Bonjour Jean,

Votre emprunt a été officiellement clôturé:

📦 Matériel: Perceuse Bosch
🏷️ Référence: PERC-001
✅ Statut: Restitué avec succès

📊 Détails de l'emprunt:
• Durée: LONG
• Restitué le: 14:30

Merci d'avoir utilisé notre service de gestion des matériels!

📈 Vous pouvez à nouveau faire une demande d'emprunt.
👍 Bon travail!
```

**Audience:** User after successful return  
**Context:** Closure confirmation  
**Action:** Encourage future use, recognize good behavior

---

## Testing Scenarios

### Scenario 1: Successful Send

```python
# Setup
client.phone = '+33612345678'
preferences.notifications_whatsapp = True

# Action
WhatsAppNotificationService.send_notification(notification)

# Expect
notification.statut == STATUT_ENVOYEE
notification.date_envoi is not None
logger.info("WhatsApp message ... sent")
```

### Scenario 2: Invalid Phone

```python
# Setup
client.phone = 'invalid_phone'

# Action
WhatsAppNotificationService.send_notification(notification)

# Expect
notification.statut == STATUT_ECHEC_PERMANENT
notification.erreur_message == "Invalid recipient phone number"
```

### Scenario 3: Twilio API Error

```python
# Setup
TWILIO_ACCOUNT_SID = 'invalid_sid'

# Action
WhatsAppNotificationService.send_notification(notification)

# Expect
notification.statut == STATUT_ECHEC
notification.nb_tentatives == 1
notification.erreur_message == "Twilio API error..."
```

### Scenario 4: Retry After Failure

```python
# Setup
notification.nb_tentatives = 0
notification.statut = STATUT_ECHEC

# Action (manual retry)
WhatsAppNotificationService.send_notification(notification)

# Expect
notification.nb_tentatives == 1
# (or STATUT_ENVOYEE if succeeds)
```

### Scenario 5: Permanent Failure After 3 Attempts

```python
# Setup
notification.nb_tentatives = 2
notification.statut = STATUT_ECHEC

# Action (third attempt)
WhatsAppNotificationService.send_notification(notification)

# Expect
notification.nb_tentatives == 3
notification.statut == STATUT_ECHEC_PERMANENT
# No more retry attempts
```

---

## Monitoring & Analytics

### Query Notification Status

```python
# Get all WhatsApp notifications
WhatsAppNotifications = NotificationLog.objects.filter(
    canal=NotificationLog.CANAL_WHATSAPP
)

# Group by status
from django.db.models import Count
by_status = WhatsAppNotifications.values('statut').annotate(count=Count('id'))

# Result:
# {'statut': 'ENVOYEE', 'count': 45}
# {'statut': 'ECHEC', 'count': 3}
# {'statut': 'ECHEC_PERMANENT', 'count': 1}
```

### Track Failures

```python
failures = NotificationLog.objects.filter(
    canal=NotificationLog.CANAL_WHATSAPP,
    statut__in=[STATUT_ECHEC, STATUT_ECHEC_PERMANENT]
).values('type_notification', 'erreur_message')

for failure in failures:
    print(f"{failure['type_notification']}: {failure['erreur_message']}")
```

### Send Rate Analysis

```python
from django.db.models import Count
from django.utils import timezone

today = timezone.now().date()
sent_today = NotificationLog.objects.filter(
    canal=NotificationLog.CANAL_WHATSAPP,
    statut=STATUT_ENVOYEE,
    date_envoi__date=today
).count()

print(f"WhatsApp messages sent today: {sent_today}")
```

---

## Troubleshooting

### Credentials Not Recognized

```bash
# Check settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.TWILIO_ACCOUNT_SID)
>>> print(settings.TWILIO_AUTH_TOKEN)
>>> print(settings.TWILIO_WHATSAPP_FROM)

# Should show actual values (not None or empty)
```

### Phone Number Invalid

```python
# Phone number must include country code
"612345678"  # ❌ Missing country code
"+33612345678"  # ✅ Correct format
"whatsapp:+33612345678"  # Format added by service

# Service auto-adds '+' if missing:
"33612345678" → "+33612345678" ✅
```

### Message Not Delivered

```python
# Check notification log
NotificationLog.objects.filter(
    id=notification_id
).values('statut', 'erreur_message', 'date_envoi')

# Check Twilio logs (via Twilio dashboard)
# - Message Activity
# - Conversation Logs
# - Error Messages
```

### Rate Limiting

```python
# Twilio free tier limits:
# - 100 messages per day
# - 1 message per second

# Check daily send rate
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

today = timezone.now().date()
sent_count = NotificationLog.objects.filter(
    canal=NotificationLog.CANAL_WHATSAPP,
    statut=NotificationLog.STATUT_ENVOYEE,
    date_envoi__date=today
).count()

if sent_count >= 100:
    print("Daily limit reached!")
```

---

## Compliance & Security

### Data Privacy

- **Phone Number Storage**: Stored in NotificationLog.destinataire
- **Message Content**: Not stored (created on-the-fly from templates)
- **Twilio Logs**: Twilio stores delivery logs per their retention policy
- **GDPR Compliance**: Phone numbers can be anonymized after 90 days

```python
# Anonymize old records
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(days=90)
NotificationLog.objects.filter(
    date_envoi__lt=cutoff,
    canal=NotificationLog.CANAL_WHATSAPP
).update(destinataire='[REDACTED]')
```

### Message Content Security

- **No Sensitive Data**: Templates don't include passwords or sensitive details
- **Reference Only**: Material codes and names only
- **Client Privacy**: First name and last name only
- **External Links**: None (no phishing risk)

### API Security

- **Credentials**: Store in environment variables only (not in code)
- **HTTPS**: Twilio enforces HTTPS for all API calls
- **Rate Limiting**: Implement on your end to prevent abuse

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(1), name='dispatch')
class SendWhatsAppView(View):
    """Prevent rapid-fire requests"""
    pass
```

---

## Performance Optimization

### Batch Sending

```python
# Inefficient: Send 100 messages one-by-one
for notification in NotificationLog.objects.filter(statut=STATUT_EN_ATTENTE):
    WhatsAppNotificationService.send_notification(notification)  # 100 calls

# Efficient: Send with slight delays
from time import sleep
for notification in NotificationLog.objects.filter(statut=STATUT_EN_ATTENTE):
    WhatsAppNotificationService.send_notification(notification)
    sleep(1)  # Respect rate limits
```

### Caching

```python
# Cache Twilio client
from django.core.cache import cache

def get_twilio_client():
    client = cache.get('twilio_client')
    if client is None:
        client = Client(account_sid, auth_token)
        cache.set('twilio_client', client, 3600)  # 1 hour
    return client
```

### Query Optimization

```python
# Before: N+1 queries
for notification in NotificationLog.objects.filter(canal=WHATSAPP):
    attribution = notification.attribution  # Query per loop
    client = attribution.client  # Another query

# After: Prefetch related
notifications = NotificationLog.objects.filter(
    canal=WHATSAPP
).select_related('attribution__client')  # 1 query + 2 joins
```

---

## Next Steps

**Phase 6:** Integration with Django signals for automatic triggering
- Auto-send WhatsApp on attribution creation
- Auto-send WhatsApp on return confirmation
- Unified multi-channel support

**Phase 7:** Dashboard and UI
- User preferences management
- Notification history view
- Admin interface for message templates
- Analytics and reporting

---

## References

- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [Message Sending Guide](https://www.twilio.com/docs/whatsapp/api/messages)
