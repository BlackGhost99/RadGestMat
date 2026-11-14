from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from assets.models import Departement
from users.models import ProfilUtilisateur


class MobileAuthTests(TestCase):
    def setUp(self):
        department = Departement.objects.create(nom="IT", code="IT")
        self.user = get_user_model().objects.create_user(username="mobile_agent", password="test-only-password")
        self.profile, _ = ProfilUtilisateur.objects.update_or_create(
            user=self.user, defaults={"departement": department, "role": "DEPT_USER", "actif": True})
        self.browser = Client(enforce_csrf_checks=True)

    def csrf(self):
        return self.browser.get(reverse("mobile_session")).json()["csrf_token"]

    def login(self):
        return self.browser.post(reverse("mobile_login"),
            {"username": self.user.username, "password": "test-only-password"},
            HTTP_X_CSRFTOKEN=self.csrf())

    def test_login_and_logout(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["account_id"], self.user.pk)
        self.assertIn("offline_until", response.json())
        self.assertTrue(self.browser.get(reverse("mobile_session")).json()["authenticated"])
        self.assertEqual(self.browser.post(reverse("mobile_logout"),
            HTTP_X_CSRFTOKEN=self.csrf()).status_code, 200)
        self.assertFalse(self.browser.get(reverse("mobile_session")).json()["authenticated"])

    def test_csrf_required(self):
        self.assertEqual(self.browser.post(reverse("mobile_login"),
            {"username": self.user.username, "password": "test-only-password"}).status_code, 403)

    def test_revoked_profile(self):
        self.assertEqual(self.login().status_code, 200)
        self.profile.actif = False
        self.profile.save()
        self.assertFalse(self.browser.get(reverse("mobile_session")).json()["authenticated"])
        self.assertEqual(self.browser.get(reverse("mobile_bootstrap")).status_code, 403)

    def test_bad_password(self):
        self.assertEqual(self.browser.post(reverse("mobile_login"),
            {"username": self.user.username, "password": "incorrect"},
            HTTP_X_CSRFTOKEN=self.csrf()).status_code, 401)
