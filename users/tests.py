from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from assets.models import Departement
from .models import ProfilUtilisateur, UserPreferences


@override_settings(SITE_URL='https://radgestmat.example', PASSWORD_RESET_TIMEOUT=86400)
class AccountAdminTests(TestCase):
    def setUp(self):
        self.dept = Departement.objects.create(nom='IT', code='IT')
        self.admin = User.objects.create_user('admin_app', password='Old-secure-123!')
        ProfilUtilisateur.objects.create(user=self.admin, departement=self.dept, role='SUPER_ADMIN')
        self.member = User.objects.create_user('member', email='member@example.com', password='Old-secure-123!')
        ProfilUtilisateur.objects.create(user=self.member, departement=self.dept)
        self.client.force_login(self.admin)

    def route(self, name, user=None):
        return reverse('users:' + name, kwargs={'pk': user.pk} if user else None)

    def form_data(self, **changes):
        return {
            'username': 'member', 'first_name': 'Jean', 'last_name': 'Test',
            'email': 'member@example.com', 'departement': self.dept.pk,
            'role': 'DEPT_USER', 'is_active': 'on', **changes,
        }

    def test_admin_role_access_and_identity(self):
        page = self.client.get(self.route('user_detail', self.member))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context['user'], self.admin)
        self.assertEqual(page.context['target'], self.member)
        self.assertEqual(self.client.get(self.route('user_list')).status_code, 200)

    def test_member_cannot_access_account_management(self):
        self.client.force_login(self.member)
        for name in ['user_detail', 'user_update', 'user_password', 'user_delete']:
            self.assertEqual(self.client.get(self.route(name, self.admin)).status_code, 403)
        self.assertEqual(self.client.post(self.route('user_send_reset', self.admin)).status_code, 403)
        self.assertEqual(self.client.get(self.route('user_list')).status_code, 403)

    def test_update_theme_and_ignore_django_elevation(self):
        response = self.client.post(self.route('user_update', self.member),
                                    self.form_data(dark_mode='on', is_superuser='on', is_staff='on'))
        self.assertRedirects(response, self.route('user_detail', self.member))
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_superuser)
        self.assertFalse(self.member.is_staff)
        self.assertTrue(UserPreferences.objects.get(user=self.member).dark_mode)
        self.client.force_login(self.member)
        session = self.client.session
        session['theme'] = 'light'
        session.save()
        self.assertEqual(self.client.get(reverse('users:user_settings')).context['theme'], 'dark')

    def test_cannot_promote_to_superadmin_or_edit_self(self):
        response = self.client.post(self.route('user_update', self.member), self.form_data(role='SUPER_ADMIN'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProfilUtilisateur.objects.get(user=self.member).role, 'DEPT_USER')
        self.assertEqual(self.client.get(self.route('user_update', self.admin)).status_code, 403)
        self.assertEqual(self.client.post(self.route('user_delete', self.admin)).status_code, 403)

    def test_protect_django_admin(self):
        root = User.objects.create_superuser('root', 'root@example.com', 'Root-secure-123!')
        self.assertEqual(self.client.post(self.route('user_send_reset', root)).status_code, 403)
        self.assertEqual(self.client.get(self.route('user_update', root)).status_code, 403)

    def test_deactivate_preserves_user(self):
        self.client.post(self.route('user_delete', self.member))
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertFalse(ProfilUtilisateur.objects.get(user=self.member).actif)

    @patch('users.account_admin.send_email', return_value=1)
    def test_email_target_and_single_use_reset(self, send):
        self.assertEqual(self.client.get(self.route('user_send_reset', self.member)).status_code, 405)
        self.assertRedirects(self.client.post(self.route('user_send_reset', self.member)),
                             self.route('user_detail', self.member))
        data = send.call_args.kwargs
        self.assertEqual(data['recipient_list'], ['member@example.com'])
        link = next(line for line in data['message'].splitlines() if line.startswith('https://'))
        self.client.logout()
        response = self.client.get(link, follow=True)
        self.assertTrue(response.context['validlink'])
        path = response.redirect_chain[-1][0]
        response = self.client.post(path, {'new_password1': 'New-Strong-776!pass',
                                           'new_password2': 'New-Strong-776!pass'})
        self.assertRedirects(response, reverse('users:password_reset_complete'))
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('New-Strong-776!pass'))
        self.assertFalse(self.client.get(link, follow=True).context['validlink'])

    @patch('users.account_admin.send_email', side_effect=RuntimeError('transport unavailable'))
    def test_failed_delivery_does_not_change_password(self, send):
        old = self.member.password
        response = self.client.post(self.route('user_send_reset', self.member), follow=True)
        self.assertContains(response, 'Envoi impossible')
        self.member.refresh_from_db()
        self.assertEqual(self.member.password, old)

    def test_admin_sets_password(self):
        self.client.post(self.route('user_password', self.member),
                         {'new_password1': 'New-Strong-776!pass', 'new_password2': 'New-Strong-776!pass'})
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password('New-Strong-776!pass'))

    def test_create_invited_account(self):
        response = self.client.post(self.route('user_create'), self.form_data(username='invite', email='invite@example.com'))
        target = User.objects.get(username='invite')
        self.assertRedirects(response, self.route('user_detail', target))
        self.assertFalse(target.has_usable_password())
        self.assertEqual(ProfilUtilisateur.objects.get(user=target).role, 'DEPT_USER')

    def test_login_member_redirects_away_from_admin_page(self):
        self.client.logout()
        target = self.route('user_detail', self.admin)
        response = self.client.post(reverse('login') + '?next=' + target,
                                    {'username': 'member', 'password': 'Old-secure-123!'})
        self.assertRedirects(response, reverse('assets:dashboard'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.member.pk)
        self.assertEqual(self.client.get(target).status_code, 403)

    def test_login_admin_preserves_authorized_destination(self):
        self.client.logout()
        target = self.route('user_detail', self.member)
        response = self.client.post(reverse('login') + '?next=' + target,
                                    {'username': 'admin_app', 'password': 'Old-secure-123!'})
        self.assertRedirects(response, target)

    def test_login_password_toggle_and_invalid_credentials(self):
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'id="password-toggle"')
        self.assertContains(response, 'autocomplete="current-password"')
        response = self.client.post(reverse('login'), {'username': 'member', 'password': 'wrong'})
        self.assertContains(response, "Nom d'utilisateur ou mot de passe incorrect.")
        self.assertNotIn('_auth_user_id', self.client.session)
