from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegisterTest(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(reverse('authentication:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_success(self):
        response = self.client.post(reverse('authentication:register'), {
            'username': 'kesya',
            'email': 'kesya@ui.ac.id',
            'password1': 'BakaraPass123!',
            'password2': 'BakaraPass123!',
        })
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertTrue(User.objects.filter(username='kesya').exists())

    def test_register_rejects_non_ui_email(self):
        response = self.client.post(reverse('authentication:register'), {
            'username': 'kesya',
            'email': 'kesya@gmail.com',
            'password1': 'BakaraPass123!',
            'password2': 'BakaraPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='kesya').exists())

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user('lama', 'kesya@ui.ac.id', 'BakaraPass123!')
        self.client.post(reverse('authentication:register'), {
            'username': 'baru',
            'email': 'KESYA@ui.ac.id',
            'password1': 'BakaraPass123!',
            'password2': 'BakaraPass123!',
        })
        self.assertFalse(User.objects.filter(username='baru').exists())


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('kesya', 'kesya@ui.ac.id', 'BakaraPass123!')

    def test_login_with_username(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'kesya', 'password': 'BakaraPass123!',
        })
        self.assertRedirects(response, reverse('main:show_beranda'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_with_email(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'kesya@ui.ac.id', 'password': 'BakaraPass123!',
        })
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_wrong_password(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'kesya', 'password': 'salah',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirects_to_next(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'kesya', 'password': 'BakaraPass123!',
            'next': reverse('main:show_profil'),
        })
        self.assertRedirects(response, reverse('main:show_profil'))

    def test_login_ignores_external_next(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'kesya', 'password': 'BakaraPass123!',
            'next': 'https://evil.com/',
        })
        self.assertRedirects(response, reverse('main:show_beranda'))

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('main:show_beranda'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('authentication:logout'))
        self.assertEqual(response.status_code, 405)


class AccessControlTest(TestCase):
    def test_protected_pages_redirect_to_login(self):
        for name in ('main:show_profil', 'main:show_transaksi'):
            url = reverse(name)
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('authentication:login')}?next={url}")

    def test_protected_pages_accessible_when_logged_in(self):
        user = User.objects.create_user('kesya', 'kesya@ui.ac.id', 'BakaraPass123!')
        self.client.force_login(user)
        for name in ('main:show_profil', 'main:show_transaksi'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_public_pages_accessible_without_login(self):
        for name in ('main:show_beranda', 'main:show_katalog', 'main:show_tentang'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
