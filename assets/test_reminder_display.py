from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from django.test import SimpleTestCase
from assets.reminder_views import display_reminder_loans


class ReminderDisplayTests(SimpleTestCase):
    def test_identical_material_deadline_grouped_without_losing_distinct_deadlines(self):
        now = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)
        def loan(material, deadline):
            return SimpleNamespace(materiel_id=material, retour_echeance=lambda: deadline)
        items = display_reminder_loans([
            loan(1, now), loan(1, now), loan(1, now + timedelta(hours=1)),
            loan(2, now), loan(2, now + timedelta(days=3)),
        ], now + timedelta(hours=2))
        self.assertEqual(len(items), 3)
        self.assertEqual([item["count"] for item in items], [2, 1, 1])
