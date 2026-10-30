import shutil
import tempfile
import uuid
from io import BytesIO
from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from authentication.forms import LoginForm, ProfileForm, RegisterForm
from authentication.models import Profile
from authentication.views import _get_or_create_sso_user, _prefill_profile_from_sso

User = get_user_model()
PASSWORD = 'RahasiaKuat#2024'
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def make_image(name='foto.png', fmt='PNG'):
    """Membuat file gambar kecil di memori untuk diunggah lewat form."""
    buffer = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buffer, format=fmt)
    content_type = f'image/{fmt.lower()}'
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def messages_of(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


# ---------------------------------------------------------------------------
# Models & signals
# ---------------------------------------------------------------------------

class UserModelTests(TestCase):
    def test_id_berupa_uuid(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(str(user), 'budi')

    def test_profile_dibuat_otomatis_oleh_signal(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(str(user.profile), 'Profil budi')

    def test_signal_tidak_membuat_profile_ganda_saat_user_disimpan_ulang(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        user.first_name = 'Budi'
        user.save()
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)


class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.profile = self.user.profile

    def test_is_complete_false_untuk_profile_kosong(self):
        self.assertFalse(self.profile.is_complete)

    def test_is_complete_true_tanpa_line_dan_foto(self):
        self.profile.full_name = 'Budi Santoso'
        self.profile.faculty = 'FASILKOM'
        self.profile.angkatan = 2023
        self.profile.whatsapp = '081234567890'
        self.assertTrue(self.profile.is_complete)

    def test_whatsapp_link(self):
        cases = {
            '': '',
            '081234567890': 'https://wa.me/6281234567890',
            '+62 812-3456-7890': 'https://wa.me/6281234567890',
            '6281234567890': 'https://wa.me/6281234567890',
            '81234567890': 'https://wa.me/6281234567890',
        }
        for number, expected in cases.items():
            with self.subTest(number=number):
                self.profile.whatsapp = number
                self.assertEqual(self.profile.whatsapp_link, expected)


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

class RegisterFormTests(TestCase):
    def form(self, **overrides):
        data = {
            'username': 'budi',
            'email': 'budi@ui.ac.id',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        data.update(overrides)
        return RegisterForm(data=data)

    def test_data_valid(self):
        form = self.form(email='  Budi@UI.ac.id ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'budi@ui.ac.id')

    def test_email_selain_ui_ditolak(self):
        form = self.form(email='budi@gmail.com')
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_duplikat_ditolak_tanpa_memperhatikan_huruf_besar(self):
        User.objects.create_user('lain', 'budi@ui.ac.id', PASSWORD)
        form = self.form(email='BUDI@ui.ac.id')
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], ['Email ini sudah terdaftar.'])

    def test_password_tidak_cocok_ditolak(self):
        form = self.form(password2='BerbedaSekali#99')
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)

    def test_login_dengan_username(self):
        form = LoginForm(data={'username': 'budi', 'password': PASSWORD})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_login_dengan_email(self):
        form = LoginForm(data={'username': 'BUDI@ui.ac.id', 'password': PASSWORD})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_user(), self.user)

    def test_password_salah_ditolak(self):
        form = LoginForm(data={'username': 'budi', 'password': 'salah'})
        self.assertFalse(form.is_valid())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfileFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.profile = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD).profile

    def form(self, files=None, **overrides):
        data = {
            'full_name': 'Budi Santoso',
            'faculty': 'FASILKOM',
            'angkatan': 2023,
            'whatsapp': '081234567890',
            'line_id': '',
        }
        data.update(overrides)
        return ProfileForm(data=data, files=files, instance=self.profile)

    def test_data_valid_tanpa_line_dan_foto(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_field_wajib(self):
        form = ProfileForm(data={}, instance=self.profile)
        self.assertFalse(form.is_valid())
        for field in ('full_name', 'faculty', 'angkatan', 'whatsapp'):
            with self.subTest(field=field):
                self.assertIn(field, form.errors)
        self.assertNotIn('line_id', form.errors)
        self.assertNotIn('photo', form.errors)

    def test_full_name_dirapikan(self):
        form = self.form(full_name='  Budi    Santoso ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['full_name'], 'Budi Santoso')

    def test_full_name_terlalu_pendek(self):
        form = self.form(full_name='B')
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)

    def test_angkatan_di_luar_rentang(self):
        for angkatan in (1949, timezone.now().year + 1):
            with self.subTest(angkatan=angkatan):
                form = self.form(angkatan=angkatan)
                self.assertFalse(form.is_valid())
                self.assertIn('angkatan', form.errors)

    def test_whatsapp_dinormalisasi(self):
        for number in ('081234567890', '+6281234567890', '62 812-3456-7890'):
            with self.subTest(number=number):
                form = self.form(whatsapp=number)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data['whatsapp'], '081234567890')

    def test_whatsapp_tidak_valid(self):
        for number in ('021234567', '0812', 'abcdefghijk'):
            with self.subTest(number=number):
                form = self.form(whatsapp=number)
                self.assertFalse(form.is_valid())
                self.assertIn('whatsapp', form.errors)

    def test_line_id_valid_dijadikan_huruf_kecil(self):
        form = self.form(line_id=' Budi.Santoso ')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['line_id'], 'budi.santoso')

    def test_line_id_tidak_valid(self):
        for line_id in ('abc', 'a' * 21, 'budi santoso', 'budi!'):
            with self.subTest(line_id=line_id):
                form = self.form(line_id=line_id)
                self.assertFalse(form.is_valid())
                self.assertIn('line_id', form.errors)

    def test_foto_valid(self):
        form = self.form(files={'photo': make_image()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_foto_format_tidak_didukung(self):
        form = self.form(files={'photo': make_image('foto.gif', 'GIF')})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['photo'], ['Foto harus berformat JPG, PNG, atau WEBP.']
        )

    def test_foto_terlalu_besar(self):
        with patch.object(ProfileForm, 'MAX_PHOTO_SIZE', 10):
            form = self.form(files={'photo': make_image()})
            self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['photo'], ['Ukuran foto maksimal 2 MB.'])


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class RegisterViewTests(TestCase):
    url = reverse('authentication:register')

    def test_get_menampilkan_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)

    def test_post_valid_membuat_user_dan_redirect_ke_login(self):
        response = self.client.post(self.url, {
            'username': 'budi',
            'email': 'budi@ui.ac.id',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertTrue(User.objects.filter(username='budi').exists())

    def test_post_tidak_valid_menampilkan_ulang_form(self):
        response = self.client.post(self.url, {
            'username': 'budi',
            'email': 'budi@gmail.com',
            'password1': PASSWORD,
            'password2': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context['form'], 'email', 'Email harus menggunakan domain @ui.ac.id.'
        )
        self.assertFalse(User.objects.exists())

    def test_user_login_diarahkan_ke_beranda(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('main:show_beranda'))


class LoginViewTests(TestCase):
    url = reverse('authentication:login')

    def setUp(self):
        self.user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)

    def test_get_menampilkan_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_berhasil_redirect_ke_beranda(self):
        response = self.client.post(self.url, {'username': 'budi', 'password': PASSWORD})
        self.assertRedirects(response, reverse('main:show_beranda'))
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))

    def test_login_dengan_email(self):
        response = self.client.post(self.url, {'username': 'budi@ui.ac.id', 'password': PASSWORD})
        self.assertRedirects(response, reverse('main:show_beranda'))

    def test_login_gagal(self):
        response = self.client.post(self.url, {'username': 'budi', 'password': 'salah'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_redirect_ke_next_yang_aman(self):
        next_url = reverse('main:show_profil')
        response = self.client.post(self.url, {
            'username': 'budi', 'password': PASSWORD, 'next': next_url,
        })
        self.assertRedirects(response, next_url)

    def test_next_ke_domain_luar_diabaikan(self):
        response = self.client.post(self.url, {
            'username': 'budi', 'password': PASSWORD, 'next': 'https://evil.com/',
        })
        self.assertRedirects(response, reverse('main:show_beranda'))

    def test_user_login_diarahkan_ke_beranda(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('main:show_beranda'))


class LogoutViewTests(TestCase):
    url = reverse('authentication:logout')

    def setUp(self):
        self.user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.client.force_login(self.user)

    def test_get_tidak_diizinkan(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_post_logout(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('main:show_beranda'))
        self.assertNotIn('_auth_user_id', self.client.session)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EditProfileViewTests(TestCase):
    url = reverse('authentication:edit_profile')

    def setUp(self):
        self.user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)

    def test_wajib_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('authentication:login')}?next={self.url}")

    def test_get_menampilkan_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profil_edit.html')
        self.assertIsInstance(response.context['form'], ProfileForm)

    def test_post_valid_menyimpan_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {
            'full_name': 'Budi Santoso',
            'faculty': 'FASILKOM',
            'angkatan': 2023,
            'whatsapp': '+62 812-3456-7890',
            'line_id': 'Budi.Santoso',
        })
        self.assertRedirects(response, reverse('main:show_profil'))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Budi Santoso')
        self.assertEqual(profile.whatsapp, '081234567890')
        self.assertEqual(profile.line_id, 'budi.santoso')
        self.assertTrue(profile.is_complete)

    def test_post_tidak_valid_tidak_menyimpan(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'full_name': 'Budi Santoso'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.user).full_name)


class SsoHelperTests(TestCase):
    def test_membuat_user_baru_dengan_password_tidak_terpakai(self):
        user = _get_or_create_sso_user('Budi.Santoso')
        self.assertEqual(user.username, 'budi.santoso')
        self.assertEqual(user.email, 'budi.santoso@ui.ac.id')
        self.assertFalse(user.has_usable_password())

    def test_memakai_user_dengan_email_yang_sama(self):
        existing = User.objects.create_user('budi_manual', 'Budi@ui.ac.id', PASSWORD)
        self.assertEqual(_get_or_create_sso_user('budi'), existing)
        self.assertEqual(User.objects.count(), 1)

    def test_username_bentrok_diberi_suffix(self):
        User.objects.create_user('budi', 'budi.lain@ui.ac.id', PASSWORD)
        User.objects.create_user('budi1', 'budi.lain2@ui.ac.id', PASSWORD)
        user = _get_or_create_sso_user('budi')
        self.assertEqual(user.username, 'budi2')

    def test_prefill_profile_dari_atribut_sso(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        _prefill_profile_from_sso(user, {'nama': 'Budi Santoso', 'npm': '2306123456'})
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'Budi Santoso')
        self.assertEqual(user.profile.angkatan, 2023)

    def test_prefill_tidak_menimpa_data_yang_sudah_ada(self):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        Profile.objects.filter(user=user).update(full_name='Nama Asli', angkatan=2021)
        _prefill_profile_from_sso(user, {'nama': 'Nama SSO', 'npm': '2306123456'})
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.full_name, 'Nama Asli')
        self.assertEqual(user.profile.angkatan, 2021)


@patch('authentication.views.CASClient')
class LoginSsoViewTests(TestCase):
    url = reverse('authentication:login_sso')
    sso_login_url = 'https://sso.ui.ac.id/cas2/login?service=test'

    def test_user_login_diarahkan_ke_beranda(self, cas_client):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('main:show_beranda'))
        cas_client.assert_not_called()

    def test_tanpa_ticket_redirect_ke_sso_dan_menyimpan_next(self, cas_client):
        cas_client.return_value.get_login_url.return_value = self.sso_login_url
        next_url = reverse('main:show_profil')
        response = self.client.get(self.url, {'next': next_url})
        self.assertRedirects(response, self.sso_login_url, fetch_redirect_response=False)
        self.assertEqual(self.client.session['sso_next'], next_url)

    def test_ticket_valid_login_dan_membuat_user(self, cas_client):
        cas_client.return_value.verify_ticket.return_value = (
            'budi', {'nama': 'Budi Santoso', 'npm': '2306123456'}, None,
        )
        response = self.client.get(self.url, {'ticket': 'ST-123'})
        self.assertRedirects(response, reverse('main:show_beranda'))

        user = User.objects.get(username='budi')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        self.assertEqual(user.profile.full_name, 'Budi Santoso')
        # WhatsApp belum diisi, jadi muncul peringatan untuk melengkapi profil.
        self.assertIn('WhatsApp', messages_of(response)[0])

    def test_ticket_valid_user_dengan_whatsapp_dapat_pesan_sukses(self, cas_client):
        user = User.objects.create_user('budi', 'budi@ui.ac.id', PASSWORD)
        Profile.objects.filter(user=user).update(whatsapp='081234567890')
        cas_client.return_value.verify_ticket.return_value = ('budi', {}, None)
        response = self.client.get(self.url, {'ticket': 'ST-123'})
        self.assertEqual(messages_of(response), ['Selamat datang, budi!'])

    def test_redirect_ke_next_yang_disimpan(self, cas_client):
        cas_client.return_value.verify_ticket.return_value = ('budi', {}, None)
        session = self.client.session
        session['sso_next'] = reverse('main:show_profil')
        session.save()
        response = self.client.get(self.url, {'ticket': 'ST-123'})
        self.assertRedirects(response, reverse('main:show_profil'))

    def test_ticket_tidak_valid(self, cas_client):
        cas_client.return_value.verify_ticket.return_value = (None, None, None)
        response = self.client.get(self.url, {'ticket': 'ST-salah'})
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(User.objects.exists())

    def test_server_sso_error(self, cas_client):
        cas_client.return_value.verify_ticket.side_effect = requests.ConnectionError
        response = self.client.get(self.url, {'ticket': 'ST-123'})
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertEqual(messages_of(response), ['Login SSO UI gagal. Silakan coba lagi.'])
