from io import BytesIO
import shutil
import tempfile
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from katalog.models import Barang

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


def create_test_image(filename='test_barang.png'):
    file_obj = BytesIO()
    image = Image.new('RGB', (100, 100), color='navy')
    image.save(file_obj, 'PNG')
    file_obj.seek(0)
    return SimpleUploadedFile(filename, file_obj.read(), content_type='image/png')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BarangAPITest(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.penjual = User.objects.create_user(
            username='penjual_ui',
            password='test-password',
        )
        self.pengguna_lain = User.objects.create_user(
            username='mahasiswa_lain',
            password='test-password',
        )
        self.barang = Barang.objects.create(
            penjual=self.penjual,
            nama='Kalkulator Casio FX-991EX',
            deskripsi='Kondisi mulus lengkap dengan tutup',
            kategori=Barang.ELEKTRONIK,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=150000,
            lokasi='Fasilkom UI',
            foto=create_test_image(),
        )
        self.list_url = reverse('katalog_api:barang-list')
        self.detail_url = reverse('katalog_api:barang-detail', args=[self.barang.id])
        self.status_url = reverse('katalog_api:barang-status', args=[self.barang.id])

        self.valid_payload = {
            'nama': 'Jaket Lab Kimia',
            'deskripsi': 'Ukuran L, dipakai 1 semester',
            'kategori': Barang.PAKAIAN,
            'jenis': Barang.JUAL,
            'kondisi': Barang.BAIK,
            'harga': 75000,
            'lokasi': 'FMIPA UI',
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], str(self.barang.id))
        self.assertEqual(response.data[0]['penjual_username'], 'penjual_ui')
        self.assertFalse(response.data[0]['bisa_diedit'])

        detail_response = self.client.get(self.detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['nama'], 'Kalkulator Casio FX-991EX')

    def test_search_filter_and_empty_results(self):
        response = self.client.get(self.list_url, {'search': 'casio'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        empty_response = self.client.get(self.list_url, {'search': 'barang-tidak-ada'})
        self.assertEqual(empty_response.status_code, status.HTTP_200_OK)
        self.assertEqual(empty_response.data, [])

    def test_missing_barang(self):
        url = reverse('katalog_api:barang-detail', args=[uuid.uuid4()])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_other_user_permissions(self):
        # Pengunjung anonim tidak boleh menambah barang
        guest_post = self.client.post(
            self.list_url,
            {**self.valid_payload, 'foto': create_test_image('guest.png')},
            format='multipart',
        )
        self.assertEqual(guest_post.status_code, status.HTTP_403_FORBIDDEN)

        # Pengguna login lain tidak boleh mengubah/menghapus barang milik penjual_ui
        self.client.force_authenticate(user=self.pengguna_lain)
        patch_resp = self.client.patch(
            self.detail_url,
            {'nama': 'Diubah Orang Lain'},
            format='json',
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_403_FORBIDDEN)

        delete_resp = self.client.delete(self.detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(Barang.objects.count(), 1)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.nama, 'Kalkulator Casio FX-991EX')

    def test_authenticated_user_can_create_barang(self):
        self.client.force_authenticate(user=self.pengguna_lain)
        payload = {**self.valid_payload, 'foto': create_test_image('jaket.png')}
        response = self.client.post(self.list_url, payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['penjual_username'], 'mahasiswa_lain')
        self.assertTrue(Barang.objects.filter(pk=response.data['id']).exists())

    def test_validation_errors(self):
        self.client.force_authenticate(user=self.penjual)

        # Nama hanya berisi spasi
        resp_nama = self.client.post(
            self.list_url,
            {**self.valid_payload, 'nama': '   ', 'foto': create_test_image('v1.png')},
            format='multipart',
        )
        self.assertEqual(resp_nama.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nama', resp_nama.data)

        # Jenis jual tetapi harga 0
        resp_harga = self.client.post(
            self.list_url,
            {**self.valid_payload, 'harga': 0, 'foto': create_test_image('v2.png')},
            format='multipart',
        )
        self.assertEqual(resp_harga.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('harga', resp_harga.data)

        # Berkas foto bukan gambar valid
        fake_file = SimpleUploadedFile('bukan_gambar.txt', b'ini teks biasa', content_type='text/plain')
        resp_foto = self.client.post(
            self.list_url,
            {**self.valid_payload, 'foto': fake_file},
            format='multipart',
        )
        self.assertEqual(resp_foto.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('foto', resp_foto.data)

    def test_owner_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.penjual)

        # PATCH sebagian field
        patch_resp = self.client.patch(
            self.detail_url,
            {'harga': 125000},
            format='json',
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.harga, 125000)
        self.assertEqual(self.barang.nama, 'Kalkulator Casio FX-991EX')

        # PUT tidak lengkap ditolak (foto wajib pada PUT penuh)
        incomplete_put = self.client.put(
            self.detail_url,
            {'nama': 'Tidak Lengkap'},
            format='json',
        )
        self.assertEqual(incomplete_put.status_code, status.HTTP_400_BAD_REQUEST)

        # PUT lengkap berhasil
        full_put = self.client.put(
            self.detail_url,
            {**self.valid_payload, 'foto': create_test_image('updated.png')},
            format='multipart',
        )
        self.assertEqual(full_put.status_code, status.HTTP_200_OK)

        # DELETE mengembalikan 204 No Content
        delete_resp = self.client.delete(self.detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(delete_resp.content, b'')
        self.assertFalse(Barang.objects.filter(pk=self.barang.id).exists())

    def test_update_status_endpoint(self):
        # Orang lain ditolak
        self.client.force_authenticate(user=self.pengguna_lain)
        forbidden_resp = self.client.post(
            self.status_url,
            {'status': Barang.SELESAI},
            format='json',
        )
        self.assertEqual(forbidden_resp.status_code, status.HTTP_403_FORBIDDEN)

        # Pemilik dengan status tidak valid ditolak
        self.client.force_authenticate(user=self.penjual)
        invalid_resp = self.client.post(
            self.status_url,
            {'status': 'status_ngasal'},
            format='json',
        )
        self.assertEqual(invalid_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Pemilik dengan status valid berhasil
        valid_resp = self.client.post(
            self.status_url,
            {'status': Barang.SELESAI},
            format='json',
        )
        self.assertEqual(valid_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(valid_resp.data['status'], Barang.SELESAI)

    def test_read_only_penjual_cannot_be_forged(self):
        self.client.force_authenticate(user=self.pengguna_lain)
        payload = {
            **self.valid_payload,
            'penjual': self.penjual.id,
            'foto': create_test_image('forged.png'),
        }
        response = self.client.post(self.list_url, payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['penjual_username'], 'mahasiswa_lain')

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.penjual)
        response = self.client.delete(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username='penjual_ui', password='test-password'))
        response = client.patch(self.detail_url, {'harga': 100000}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username='penjual_ui', password='test-password')

        # Ambil token CSRF dari halaman Browsable API
        page = client.get(self.list_url, HTTP_ACCEPT='text/html')
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies['csrftoken'].value

        response = client.patch(
            self.detail_url,
            {'harga': 100000},
            format='json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)