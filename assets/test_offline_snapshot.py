from django.test import TestCase
from django.contrib.auth.models import User
from assets.models import Departement, Client
from users.models import ProfilUtilisateur

class OfflineSnapshotTests(TestCase):
    def test_requires_login(self):
        self.assertEqual(self.client.get("/api/offline/v1/snapshot/").status_code, 401)

    def test_snapshot_minimizes_client_data_and_etag(self):
        dept = Departement.objects.create(code="OFF", nom="Offline")
        user = User.objects.create_user(username="offline_test", password="test")
        ProfilUtilisateur.objects.update_or_create(user=user, defaults=dict(departement=dept, role="DEPT_USER", actif=True))
        Client.objects.create(nom="Client test", email="private@example.invalid", departement=dept)
        self.client.force_login(user)
        response = self.client.get("/api/offline/v1/snapshot/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("email", response.json()["clients"][0])
        self.assertEqual(self.client.get("/api/offline/v1/snapshot/", HTTP_IF_NONE_MATCH=response["ETag"]).status_code, 304)
