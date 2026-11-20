import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient, APITestCase

from .models import Profile

User = get_user_model()
PASSWORD = 'RahasiaUI123!'


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('kesya_ui', 'kesya@ui.ac.id', PASSWORD)
        self.register_url = reverse('authentication_api:api_register')
        self.login_url = reverse('authentication_api:api_login')
        self.logout_url = reverse('authentication_api:api_logout')
        self.profile_url = reverse('authentication_api:api_profile')
        self.registration = {
            'username': 'mahasiswa_baru', 'email': 'Mahasiswa.Baru@UI.AC.ID',
            'password': PASSWORD, 'password_confirm': PASSWORD,
            'full_name': 'Mahasiswa Baru UI',
        }
        self.profile_data = {
            'full_name': '  Kesya   Clara Dania ', 'faculty': 'FASILKOM',
            'angkatan': timezone.now().year, 'whatsapp': '+62 812-3456-7890',
            'line_id': 'Kesya.Line',
        }

    def test_register_creates_user_and_single_profile_without_logging_in(self):
        response = self.client.post(self.register_url, self.registration, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['status'])
        user = User.objects.get(username='mahasiswa_baru')
        self.assertEqual(user.email, 'mahasiswa.baru@ui.ac.id')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        self.assertEqual(user.profile.full_name, 'Mahasiswa Baru UI')
        self.assertNotIn('password', response.data['user'])
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registration_supports_web_password_field_names(self):
        data = dict(self.registration)
        data['password1'] = data.pop('password')
        data['password2'] = data.pop('password_confirm')
        self.assertEqual(self.client.post(self.register_url, data).status_code, 201)

    def test_registration_rejects_invalid_data_without_creating_user(self):
        initial_count = User.objects.count()
        cases = [
            {'email': 'user@gmail.com'}, {'email': 'bad@@ui.ac.id'},
            {'email': 'KESYA@UI.AC.ID'}, {'username': 'KESYA_UI'},
            {'username': 'invalid name'}, {'password_confirm': 'different'},
            {'password': '123', 'password_confirm': '123'},
            {'password': '123456789', 'password_confirm': '123456789'},
            {'full_name': 'A'},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post(self.register_url, self.registration | changes, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.data['status'])
                self.assertEqual(User.objects.count(), initial_count)

    def test_login_by_username_and_email_then_logout_clears_session(self):
        for credentials in ({'username': self.user.username}, {'email': 'KESYA@UI.AC.ID'}):
            with self.subTest(credentials=credentials):
                response = self.client.post(self.login_url, credentials | {'password': PASSWORD}, format='json')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['user']['id'], str(self.user.pk))
                self.assertEqual(self.client.get(self.profile_url).status_code, 200)
                self.assertEqual(self.client.post(self.logout_url).status_code, 200)
                self.assertEqual(self.client.get(self.profile_url).status_code, 403)
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_rejects_missing_wrong_and_inactive_credentials(self):
        self.assertEqual(self.client.post(self.login_url, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.login_url, {
            'username': self.user.username, 'password': 'wrong',
        }).status_code, 401)
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.post(self.login_url, {
            'username': self.user.username, 'password': PASSWORD,
        }).status_code, 401)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_profile_and_logout_require_authentication(self):
        for method in ('get', 'put', 'patch'):
            self.assertEqual(getattr(self.client, method)(self.profile_url).status_code, 403)
        self.assertEqual(self.client.post(self.logout_url).status_code, 403)

    def test_profile_update_normalizes_data_and_cannot_change_account(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.profile_url, self.profile_data | {
            'id': '00000000-0000-0000-0000-000000000000',
            'username': 'hacked', 'email': 'other@ui.ac.id',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        profile = response.data['profile']
        self.assertEqual(profile['full_name'], 'Kesya Clara Dania')
        self.assertEqual(profile['whatsapp'], '081234567890')
        self.assertEqual(profile['line_id'], 'kesya.line')
        self.assertEqual(profile['whatsapp_link'], 'https://wa.me/6281234567890')
        self.assertTrue(profile['is_complete'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'kesya_ui')
        self.assertEqual(self.user.email, 'kesya@ui.ac.id')

    def test_partial_profile_can_be_completed_one_field_at_a_time(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.profile_url, {'full_name': 'Kesya Clara'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['profile']['is_complete'])
        self.assertEqual(self.client.put(self.profile_url, {'full_name': 'Kesya Clara'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(self.profile_url, self.profile_data, format='json').status_code, 200)

    def test_invalid_profile_does_not_change_saved_data(self):
        self.client.force_authenticate(self.user)
        for field, value in (
            ('faculty', 'INVALID'), ('full_name', 'A'), ('full_name', ''),
            ('angkatan', 1949), ('angkatan', timezone.now().year + 1),
            ('angkatan', None), ('whatsapp', 'abc'), ('line_id', 'bad id!'),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.patch(self.profile_url, {field: value}, format='json')
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data['errors'])
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.full_name)

    def test_profile_is_scoped_to_current_user_and_recovers_missing_profile(self):
        other = User.objects.create_user('other', 'other@ui.ac.id', PASSWORD)
        self.user.profile.delete()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.profile_url).status_code, 200)
        self.client.patch(self.profile_url, {'full_name': 'Kesya Clara'}, format='json')
        other.profile.refresh_from_db()
        self.assertEqual(other.profile.full_name, '')

    def test_photo_upload_and_validation(self):
        self.client.force_authenticate(self.user)
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            buffer = BytesIO()
            Image.new('RGB', (10, 10)).save(buffer, format='PNG')
            photo = SimpleUploadedFile('profile.png', buffer.getvalue(), content_type='image/png')
            response = self.client.patch(self.profile_url, {'photo': photo}, format='multipart')
            self.assertEqual(response.status_code, 200)
            self.assertIn('/media/profile_photos/', response.data['profile']['photo'])
            invalid = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
            self.assertEqual(self.client.patch(self.profile_url, {'photo': invalid}, format='multipart').status_code, 400)
            for image_format in ('BMP', 'PNG'):
                buffer = BytesIO()
                Image.new('RGB', (10, 10)).save(buffer, format=image_format)
                content = buffer.getvalue()
                if image_format == 'PNG':
                    content += b'0' * (2 * 1024 * 1024)
                photo = SimpleUploadedFile('profile.img', content)
                self.assertEqual(self.client.patch(self.profile_url, {'photo': photo}, format='multipart').status_code, 400)

    def test_malformed_payload_and_method_restrictions(self):
        self.assertEqual(self.client.post(self.login_url, '{bad', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(self.register_url, [], format='json').status_code, 400)
        for url in (self.login_url, self.register_url):
            self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.logout_url).status_code, 405)
        self.assertEqual(self.client.post(self.profile_url).status_code, 405)

    def test_real_session_requires_csrf_for_login_profile_and_logout(self):
        client = APIClient(enforce_csrf_checks=True)
        credentials = {'username': self.user.username, 'password': PASSWORD}
        self.assertEqual(client.post(self.login_url, credentials).status_code, 403)
        self.assertEqual(client.post(self.register_url, self.registration).status_code, 403)
        token = client.get(reverse('authentication_api:api_csrf')).data['csrfToken']
        response = client.post(self.login_url, credentials, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        token = response.data['csrfToken']
        self.assertEqual(client.patch(self.profile_url, self.profile_data, format='json').status_code, 403)
        self.assertEqual(client.patch(self.profile_url, self.profile_data, format='json', HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post(self.logout_url).status_code, 403)
        self.assertEqual(client.post(self.logout_url, HTTP_X_CSRFTOKEN=token).status_code, 200)
