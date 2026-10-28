import io
import uuid
from PIL import Image

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile

from katalog.models import Barang
from katalog.forms import BarangForm

User = get_user_model()


def create_dummy_image(filename='test_image.jpg'):
    """Helper untuk membuat berkas gambar valid dalam memori."""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color=(245, 166, 35))
    image.save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile(filename, file.read(), content_type='image/jpeg')


class BarangModelTest(TestCase):
    """Pengujian Unit untuk Model Barang."""

    def setUp(self):
        self.pemilik = User.objects.create_user(
            username='pemilik_barang',
            password='password123',
            email='pemilik@ui.ac.id'
        )
        self.pengguna_lain = User.objects.create_user(
            username='pengguna_lain',
            password='password123',
            email='lain@ui.ac.id'
        )
        self.admin_user = User.objects.create_user(
            username='admin_staff',
            password='password123',
            email='admin@ui.ac.id',
            is_staff=True
        )

        self.barang_jual = Barang.objects.create(
            penjual=self.pemilik,
            nama='Kalkulator Casio FX-991EX',
            kategori=Barang.ELEKTRONIK,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=150000,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('kalkulator.jpg')
        )
        self.barang_donasi = Barang.objects.create(
            penjual=self.pemilik,
            nama='Buku Catatan Kalkulus',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            kondisi=Barang.LAYAK_PAKAI,
            harga=None,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('buku.jpg')
        )

    def test_harga_display_jual(self):
        """Memastikan harga_display untuk barang dijual diformat 'Rp ...'."""
        self.assertEqual(self.barang_jual.harga_display, 'Rp 150.000')

    def test_harga_display_donasi_dan_harga_none(self):
        """Memastikan harga_display bernilai 'Gratis' jika harga None atau 0."""
        self.assertEqual(self.barang_donasi.harga_display, 'Gratis')

        self.barang_jual.harga = 0
        self.assertEqual(self.barang_jual.harga_display, 'Gratis')

        self.barang_jual.harga = None
        self.assertEqual(self.barang_jual.harga_display, 'Gratis')

    def test_permission_bisa_diedit_oleh(self):
        """Memastikan hanya pemilik barang atau staf admin yang dapat mengedit."""
        self.assertTrue(self.barang_jual.bisa_diedit_oleh(self.pemilik))
        self.assertFalse(self.barang_jual.bisa_diedit_oleh(self.pengguna_lain))
        self.assertTrue(self.barang_jual.bisa_diedit_oleh(self.admin_user))
        self.assertFalse(self.barang_jual.bisa_diedit_oleh(AnonymousUser()))

    def test_permission_bisa_dihapus_oleh(self):
        """Memastikan hanya pemilik barang atau staf admin yang dapat menghapus."""
        self.assertTrue(self.barang_jual.bisa_dihapus_oleh(self.pemilik))
        self.assertFalse(self.barang_jual.bisa_dihapus_oleh(self.pengguna_lain))
        self.assertTrue(self.barang_jual.bisa_dihapus_oleh(self.admin_user))
        self.assertFalse(self.barang_jual.bisa_dihapus_oleh(AnonymousUser()))


class BarangFormTest(TestCase):
    """Pengujian Unit untuk Form Validasi BarangForm."""

    def test_form_valid_jual(self):
        """Form valid jika semua field wajib terisi dan harga jual > 0."""
        data = {
            'nama': 'Meja Belajar Minimalis',
            'deskripsi': 'Meja kokoh ukuran 100x50 cm.',
            'kategori': 'furnitur',
            'jenis': 'jual',
            'kondisi': 'baik',
            'harga': 120000,
            'lokasi': 'Kukusan Teknik',
        }
        files = {'foto': create_dummy_image('meja.jpg')}
        form = BarangForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_foto_kosong(self):
        """Form invalid jika foto tidak diunggah pada pembuatan barang baru."""
        data = {
            'nama': 'Jaket Kuning UI',
            'kategori': 'pakaian',
            'jenis': 'jual',
            'kondisi': 'baru',
            'harga': 90000,
        }
        form = BarangForm(data=data, files={})
        self.assertFalse(form.is_valid())
        self.assertIn('foto', form.errors)

    def test_form_invalid_nama_kosong(self):
        """Form invalid jika nama barang kosong."""
        data = {
            'nama': '',
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baru',
            'harga': 50000,
        }
        files = {'foto': create_dummy_image()}
        form = BarangForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('nama', form.errors)

    def test_form_invalid_harga_nol_atau_kosong_pada_jual(self):
        """Form invalid jika jenis jual memiliki harga <= 0 atau kosong."""
        # Kasus harga 0
        form_zero = BarangForm(
            data={
                'nama': 'Keyboard Mekanikal',
                'kategori': 'elektronik',
                'jenis': 'jual',
                'kondisi': 'baik',
                'harga': 0,
            },
            files={'foto': create_dummy_image()}
        )
        self.assertFalse(form_zero.is_valid())
        self.assertIn('harga', form_zero.errors)

        # Kasus harga negatif
        form_neg = BarangForm(
            data={
                'nama': 'Keyboard Mekanikal',
                'kategori': 'elektronik',
                'jenis': 'jual',
                'kondisi': 'baik',
                'harga': -5000,
            },
            files={'foto': create_dummy_image()}
        )
        self.assertFalse(form_neg.is_valid())
        self.assertIn('harga', form_neg.errors)

        # Kasus harga kosong pada jual
        form_empty = BarangForm(
            data={
                'nama': 'Keyboard Mekanikal',
                'kategori': 'elektronik',
                'jenis': 'jual',
                'kondisi': 'baik',
                'harga': '',
            },
            files={'foto': create_dummy_image()}
        )
        self.assertFalse(form_empty.is_valid())
        self.assertIn('harga', form_empty.errors)

    def test_form_donasi_mengosongkan_harga(self):
        """Form mengosongkan harga (harga = None) jika jenisnya donasi meskipun input terisi."""
        data = {
            'nama': 'Novel Fiksi Ilmiah',
            'kategori': 'buku',
            'jenis': 'donasi',
            'kondisi': 'baik',
            'harga': 75000,  # Nilai yang seharusnya di-reset jadi None
        }
        files = {'foto': create_dummy_image('novel.jpg')}
        form = BarangForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['harga'])


class BarangViewTest(TestCase):
    """Pengujian Unit untuk Views dan HTTP Status Modul Katalog."""

    def setUp(self):
        self.client = Client()
        self.pemilik = User.objects.create_user(
            username='penjual_katalog',
            password='password123',
            email='penjual@ui.ac.id'
        )
        self.pembeli = User.objects.create_user(
            username='calon_pembeli',
            password='password123',
            email='pembeli@ui.ac.id'
        )
        self.admin = User.objects.create_user(
            username='admin_moderator',
            password='password123',
            email='moderator@ui.ac.id',
            is_staff=True
        )

        self.barang = Barang.objects.create(
            penjual=self.pemilik,
            nama='Lampu Meja LED',
            kategori=Barang.FURNITUR,
            jenis=Barang.JUAL,
            kondisi=Barang.BARU,
            harga=65000,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('lampu.jpg')
        )

    def test_get_katalog_success_dan_template(self):
        """GET /katalog/ menghasilkan status 200 dan render template katalog/katalog.html."""
        response = self.client.get('/katalog/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'katalog/katalog.html')

    def test_get_detail_barang_exists_dan_404_uuid_acak(self):
        """GET /katalog/<uuid:pk>/ 200 untuk barang ada dan 404 untuk UUID acak."""
        # Barang yang ada
        response = self.client.get(f'/katalog/{self.barang.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'katalog/detail_barang.html')

        # UUID acak yang tidak terdaftar
        random_id = uuid.uuid4()
        response_404 = self.client.get(f'/katalog/{random_id}/')
        self.assertEqual(response_404.status_code, 404)

    def test_tambah_barang_unauthenticated_redirect_302(self):
        """Pengguna yang belum login diarahkan (302) ke halaman login saat akses tambah barang."""
        response = self.client.get('/katalog/tambah/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login') or '/auth/login' in response.url)

    def test_user_lain_edit_atau_hapus_mendapat_permission_denied_403(self):
        """Pengguna lain yang mencoba mengedit atau menghapus barang orang lain mendapat HTTP 403."""
        self.client.login(username='calon_pembeli', password='password123')

        # Percobaan Edit
        res_edit = self.client.get(f'/katalog/{self.barang.id}/edit/')
        self.assertEqual(res_edit.status_code, 403)

        # Percobaan Hapus
        res_hapus = self.client.post(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_hapus.status_code, 403)

    def test_staff_admin_dapat_hapus_barang_orang_lain(self):
        """Staff/Admin memiliki wewenang untuk menghapus barang listing milik pengguna lain."""
        self.client.login(username='admin_moderator', password='password123')
        res_hapus = self.client.post(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_hapus.status_code, 302)
        self.assertFalse(Barang.objects.filter(id=self.barang.id).exists())


class BarangAjaxJsonTest(TestCase):
    """Pengujian Unit untuk Endpoint JSON dan AJAX Modul Katalog."""

    def setUp(self):
        self.client = Client()
        self.pemilik = User.objects.create_user(
            username='ajax_tester',
            password='password123',
            email='ajax@ui.ac.id'
        )
        self.barang = Barang.objects.create(
            penjual=self.pemilik,
            nama='Earphone Type-C',
            kategori=Barang.ELEKTRONIK,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=35000,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('earphone.jpg')
        )

    def test_get_katalog_json_array_status_200(self):
        """GET /katalog/json/ mengembalikan JSON array data barang aktif dengan status 200."""
        response = self.client.get('/katalog/json/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        first_item = data[0]
        self.assertIn('id', first_item)
        self.assertIn('nama', first_item)
        self.assertIn('harga', first_item)
        self.assertIn('foto_url', first_item)
        self.assertEqual(first_item['nama'], 'Earphone Type-C')

    def test_tambah_barang_ajax_valid_status_201(self):
        """POST ke endpoint tambah barang AJAX mengembalikan status 201 jika data form valid."""
        self.client.login(username='ajax_tester', password='password123')
        data = {
            'nama': 'Mouse Wireless Silent',
            'deskripsi': 'Mouse bluetooth baterai awet',
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baru',
            'harga': 75000,
            'lokasi': 'Perpustakaan UI',
            'foto': create_dummy_image('mouse.jpg'),
        }
        response = self.client.post('/katalog/tambah-ajax/', data)
        self.assertEqual(response.status_code, 201)

        res_data = response.json()
        self.assertEqual(res_data['nama'], 'Mouse Wireless Silent')
        self.assertEqual(res_data['harga'], 75000)
        self.assertTrue(Barang.objects.filter(nama='Mouse Wireless Silent').exists())

    def test_tambah_barang_ajax_invalid_status_400(self):
        """POST ke endpoint tambah barang AJAX mengembalikan status 400 jika data form tidak lengkap."""
        self.client.login(username='ajax_tester', password='password123')
        # Kirim data tanpa nama dan tanpa foto
        data = {
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baru',
            'harga': 50000,
        }
        response = self.client.post('/katalog/tambah-ajax/', data)
        self.assertEqual(response.status_code, 400)

        res_data = response.json()
        self.assertIn('errors', res_data)
