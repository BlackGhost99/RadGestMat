from unittest.mock import patch
from django.test import SimpleTestCase

class IntegrationTests(SimpleTestCase):
    @patch.dict("os.environ", {"REMINDER_JOB_TOKEN": ""})
    def test_missing_secret_rejects_requests(self):
        self.assertEqual(self.client.post("/api/internal/reminder-tick/").status_code, 403)

    @patch.dict("os.environ", {"REMINDER_JOB_TOKEN": "test-only"})
    def test_wrong_secret_rejected(self):
        self.assertEqual(self.client.post("/api/internal/reminder-tick/", HTTP_AUTHORIZATION="Bearer wrong").status_code, 403)

    @patch.dict("os.environ", {"ANDROID_CERT_SHA256": "invalid"})
    def test_invalid_certificate_unavailable(self):
        self.assertEqual(self.client.get("/.well-known/assetlinks.json").status_code, 503)

    @patch.dict("os.environ", {"ANDROID_CERT_SHA256": ":".join(["AA"] * 32)})
    def test_valid_certificate(self):
        response = self.client.get("/.well-known/assetlinks.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["target"]["package_name"], "com.radgestmat.app")
