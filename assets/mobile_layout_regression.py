"""Browser regression for the compact mobile inventory (run separately in CI)."""
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from playwright.sync_api import sync_playwright

from assets.models import Departement, Materiel
from users.models import ProfilUtilisateur


class MobileInventoryLayoutTest(StaticLiveServerTestCase):
    def test_inventory_starts_below_header_and_table_scrolls(self):
        dept = Departement.objects.create(code='MOB', nom='Mobile test')
        user = User.objects.create_user('mobile-test', password='test-only-password')
        ProfilUtilisateur.objects.create(user=user, departement=dept, role='SUPER_ADMIN')
        Materiel.objects.bulk_create([
            Materiel(departement=dept, asset_id=f'MOB-{i}', numero_inventaire=f'INV-MOB-{i}',
                     nom=f'Matériel {i:02d}')
            for i in range(35)
        ])
        self.client.force_login(user)
        cookie = self.client.cookies['sessionid'].value
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width, height in [(320, 640), (390, 780), (768, 1024)]:
                    with self.subTest(width=width, height=height):
                        context = browser.new_context(viewport={'width': width, 'height': height},
                                                      is_mobile=True, has_touch=True)
                        context.add_cookies([{'name': 'sessionid', 'value': cookie,
                                              'url': self.live_server_url}])
                        page = context.new_page()
                        # Keep the test deterministic and avoid external resources / live reminders.
                        page.route('**/*', lambda route: route.continue_()
                                   if route.request.url.startswith(self.live_server_url)
                                   and '/api/reminders/web/' not in route.request.url
                                   else route.abort())
                        page.goto(self.live_server_url + reverse('assets:materiel_list'))
                        page.locator('.inventory-heading').wait_for()
                        self.assertEqual(page.locator('#web-reminders').count(), 0)
                        self.assertTrue(page.locator('#notification-bell').is_visible())
                        self.assertIn('/notifications/dashboard/', page.locator('#notification-bell').get_attribute('href'))
                        self.assertLessEqual(page.locator('#notification-bell').bounding_box()['x'] + page.locator('#notification-bell').bounding_box()['width'], width)
                        header = page.locator('.app-header').bounding_box()
                        heading = page.locator('.inventory-heading').bounding_box()
                        table = page.locator('#group-table-wrapper').bounding_box()
                        nav = page.locator('.mobile-bottom-nav').bounding_box()
                        self.assertLessEqual(header['y'], 2)
                        self.assertGreaterEqual(heading['y'], header['y'] + header['height'] - 2)
                        self.assertLessEqual(heading['y'] - header['y'] - header['height'], 24)
                        self.assertGreaterEqual(table['height'], 120)
                        self.assertLessEqual(table['y'] + table['height'], nav['y'] + 2)
                        self.assertTrue(page.locator('#group-table-wrapper').evaluate(
                            'e => e.scrollHeight > e.clientHeight'))
                        context.close()
            finally:
                browser.close()
