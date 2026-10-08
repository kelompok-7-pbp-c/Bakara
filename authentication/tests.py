import io
import shutil
import tempfile
from unittest.mock import patch

from PIL import Image

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from authentication.forms import ProfileForm
from authentication.models import Profile


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


def make_image(name='foto.png', fmt='PNG', size=(10, 10)):
    buffer = io.BytesIO()
    Image.new('RGB', size, 'gold').save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


MEDIA_ROOT_TEST = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEST)
class ProfileTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT_TEST, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user('kesya', 'kesya@ui.ac.id', 'BakaraPass123!')
        self.client.force_login(self.user)
        self.valid_data = {
            'full_name': 'Kesya Clara', 'faculty': 'FASILKOM', 'angkatan': 2023,
            'whatsapp': '081234567890', 'line_id': 'kesya.clara',
        }

    def post_profile(self, photo=True, **overrides):
        data = {**self.valid_data, **overrides}
        if photo:
            data['photo'] = make_image()
        return self.client.post(reverse('authentication:edit_profile'), data)

    def test_profile_page_creates_empty_profile(self):
        response = self.client.get(reverse('main:show_profil'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profil kamu belum lengkap')
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_page_shows_data(self):
        self.post_profile()
        response = self.client.get(reverse('main:show_profil'))
        self.assertContains(response, 'Kesya Clara')
        self.assertContains(response, 'Fakultas Ilmu Komputer')
        self.assertContains(response, '2023')
        self.assertContains(response, 'https://wa.me/6281234567890')
        self.assertContains(response, 'kesya.clara')
        self.assertContains(response, 'profile_photos/')
        self.assertNotContains(response, 'Profil kamu belum lengkap')

    def test_edit_profile_success(self):
        response = self.post_profile()
        self.assertRedirects(response, reverse('main:show_profil'))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Kesya Clara')
        self.assertEqual(profile.faculty, 'FASILKOM')
        self.assertEqual(profile.angkatan, 2023)
        self.assertEqual(profile.whatsapp, '081234567890')
        self.assertEqual(profile.line_id, 'kesya.clara')
        self.assertTrue(profile.photo)
        self.assertTrue(profile.is_complete)

    def test_edit_profile_requires_all_fields(self):
        response = self.client.post(reverse('authentication:edit_profile'), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['form'].errors),
            {'photo', 'full_name', 'faculty', 'angkatan', 'whatsapp', 'line_id'},
        )

    def test_edit_profile_requires_photo(self):
        response = self.post_profile(photo=False)
        self.assertIn('photo', response.context['form'].errors)

    def test_edit_profile_keeps_existing_photo(self):
        self.post_profile()
        old_photo = Profile.objects.get(user=self.user).photo.name
        response = self.post_profile(photo=False, full_name='Kesya Baru')
        self.assertRedirects(response, reverse('main:show_profil'))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Kesya Baru')
        self.assertEqual(profile.photo.name, old_photo)

    def test_edit_profile_rejects_non_image_photo(self):
        data = {**self.valid_data, 'photo': SimpleUploadedFile('foto.png', b'bukan gambar')}
        response = self.client.post(reverse('authentication:edit_profile'), data)
        self.assertIn('photo', response.context['form'].errors)

    def test_edit_profile_rejects_large_photo(self):
        with patch.object(ProfileForm, 'MAX_PHOTO_SIZE', 10):
            response = self.post_profile()
        self.assertIn('photo', response.context['form'].errors)

    def test_edit_profile_rejects_unsupported_photo_format(self):
        data = {**self.valid_data, 'photo': make_image('foto.gif', 'GIF')}
        response = self.client.post(reverse('authentication:edit_profile'), data)
        self.assertIn('photo', response.context['form'].errors)

    def test_edit_profile_normalizes_whatsapp(self):
        for number in ('+62 812-3456-7890', '6281234567890', '0812 3456 7890'):
            self.post_profile(whatsapp=number)
            self.assertEqual(Profile.objects.get(user=self.user).whatsapp, '081234567890')

    def test_edit_profile_rejects_invalid_whatsapp(self):
        for number in ('12345', '0212345678', 'abc081234567'):
            response = self.post_profile(whatsapp=number)
            self.assertIn('whatsapp', response.context['form'].errors)

    def test_edit_profile_rejects_invalid_line_id(self):
        for line_id in ('abc', 'kesya clara', 'a' * 21, 'kesya!'):
            response = self.post_profile(line_id=line_id)
            self.assertIn('line_id', response.context['form'].errors)

    def test_edit_profile_rejects_invalid_angkatan(self):
        for angkatan in (1900, timezone.now().year + 1):
            data = {**self.valid_data, 'angkatan': angkatan}
            response = self.client.post(reverse('authentication:edit_profile'), data)
            self.assertIn('angkatan', response.context['form'].errors)

    def test_edit_profile_rejects_unknown_faculty(self):
        data = {**self.valid_data, 'faculty': 'XYZ'}
        response = self.client.post(reverse('authentication:edit_profile'), data)
        self.assertIn('faculty', response.context['form'].errors)

    def test_edit_profile_requires_login(self):
        self.client.logout()
        url = reverse('authentication:edit_profile')
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('authentication:login')}?next={url}")


class SSOLoginTest(TestCase):
    @patch('authentication.views.CASClient')
    def test_sso_login_creates_user_and_prefills_profile(self, cas_client):
        cas_client.return_value.verify_ticket.return_value = (
            'kesya.clara', {'nama': 'Kesya Clara', 'npm': '2306123456'}, None,
        )
        response = self.client.get(reverse('authentication:login_sso'), {'ticket': 'ST-1'})
        self.assertRedirects(response, reverse('main:show_beranda'))

        user = User.objects.get(username='kesya.clara')
        self.assertEqual(user.email, 'kesya.clara@ui.ac.id')
        self.assertEqual(user.profile.full_name, 'Kesya Clara')
        self.assertEqual(user.profile.angkatan, 2023)

    @patch('authentication.views.CASClient')
    def test_sso_login_keeps_existing_profile(self, cas_client):
        user = User.objects.create_user('kesya', 'kesya@ui.ac.id', 'BakaraPass123!')
        Profile.objects.create(user=user, full_name='Nama Pilihan', faculty='FT', angkatan=2022)
        cas_client.return_value.verify_ticket.return_value = (
            'kesya', {'nama': 'Nama Dari SSO', 'npm': '2306123456'}, None,
        )
        self.client.get(reverse('authentication:login_sso'), {'ticket': 'ST-1'})

        user.profile.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'Nama Pilihan')
        self.assertEqual(user.profile.angkatan, 2022)
