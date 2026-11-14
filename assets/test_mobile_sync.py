from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from assets.models import Departement, Materiel
from users.models import ProfilUtilisateur


class MobileBootstrapTests(TestCase):
    def setUp(self):
        self.a = Departement.objects.create(nom="IT", code="IT")
        self.b = Departement.objects.create(nom="Finance", code="FIN")
        self.one = Materiel.objects.create(nom="PC", departement=self.a, asset_id="OKP-000001", numero_inventaire="RAD-000001")
        self.two = Materiel.objects.create(nom="Printer", departement=self.b, asset_id="OKP-000002", numero_inventaire="RAD-000002")
        self.url = reverse("mobile_bootstrap")

    def test_anonymous(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_missing_profile(self):
        user = get_user_model().objects.create_user(username="missing")
        ProfilUtilisateur.objects.filter(user=user).delete()
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_department_scope_and_revocation(self):
        user = get_user_model().objects.create_user(username="agent")
        profile, _ = ProfilUtilisateur.objects.update_or_create(user=user, defaults={"departement": self.a, "role": "DEPT_USER", "actif": True})
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["id"] for m in response.json()["materiels"]], [self.one.pk])
        self.assertIn("no-store", response["Cache-Control"])
        profile.actif = False
        profile.save()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_superuser_scope(self):
        user = get_user_model().objects.create_superuser(username="root", email="root@example.invalid", password="test-only-password")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["materiels"]), 2)
        self.assertEqual(self.client.post(self.url).status_code, 405)
