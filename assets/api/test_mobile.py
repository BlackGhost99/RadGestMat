"""Tests for the versioned, read-only mobile API."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from assets.models import Departement, Materiel
from users.models import ProfilUtilisateur


class MobileInventoryApiTests(TestCase):
    def setUp(self):
        self.department = Departement.objects.create(code="MOB", nom="Mobile")
        self.other_department = Departement.objects.create(code="OTH", nom="Other")
        self.user = User.objects.create_user(username="mobile-user", password="safe-test-password")
        ProfilUtilisateur.objects.create(
            user=self.user,
            departement=self.department,
            role="DEPT_USER",
            actif=True,
        )
        self.asset = Materiel.objects.create(
            asset_id="MOBILE-001",
            numero_inventaire="MOB-INV-001",
            nom="Scanner test",
            departement=self.department,
            statut_disponibilite=Materiel.STATUT_DISPONIBLE,
        )
        self.other_asset = Materiel.objects.create(
            asset_id="OTHER-001",
            numero_inventaire="OTH-INV-001",
            nom="Autre département",
            departement=self.other_department,
            statut_disponibilite=Materiel.STATUT_DISPONIBLE,
        )
        self.client = APIClient()

    def test_requires_authentication(self):
        response = self.client.get("/api/v1/mobile/assets/")
        self.assertEqual(response.status_code, 401)

    def test_list_is_scoped_to_users_department(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/mobile/assets/")
        self.assertEqual(response.status_code, 200)
        asset_ids = [item["asset_id"] for item in response.data["results"]]
        self.assertIn(self.asset.asset_id, asset_ids)
        self.assertNotIn(self.other_asset.asset_id, asset_ids)

    def test_qr_identifier_resolves_only_authorized_assets(self):
        self.client.force_login(self.user)
        response = self.client.get(f"/api/v1/mobile/assets/{self.asset.asset_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["asset_id"], self.asset.asset_id)

        forbidden_asset = self.client.get(f"/api/v1/mobile/assets/{self.other_asset.asset_id}/")
        self.assertEqual(forbidden_asset.status_code, 404)

    def test_invalid_pagination_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/mobile/assets/?limit=1000")
        self.assertEqual(response.status_code, 400)

    def test_inactive_profile_is_forbidden(self):
        profile = self.user.profilutilisateur
        profile.actif = False
        profile.save(update_fields=["actif"])
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/mobile/assets/")
        self.assertEqual(response.status_code, 403)
