import io
import uuid
from PIL import Image

from django import forms
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile

from katalog.models import Barang
from katalog.forms import BarangForm
from minat.models import MinatBarang

User = get_user_model()


def create_dummy_image(filename='test_image.jpg', size_bytes=None, is_valid_image=True):
    """Helper untuk membuat berkas gambar dalam memori (valid, oversized, atau korup)."""
    if not is_valid_image:
        return SimpleUploadedFile(filename, b'not_an_image_content', content_type='image/jpeg')

    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color=(245, 166, 35))
    image.save(file, 'jpeg')
    content = file.getvalue()

    if size_bytes and size_bytes > len(content):
        # Tambah padding byte agar melebihi batas ukuran
        content = content + b'0' * (size_bytes - len(content))

    return SimpleUploadedFile(filename, content, content_type='image/jpeg')


class BarangModelTest(TestCase):
    """Pengujian Unit untuk Model Barang dan QuerySet."""

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
        self.super_user = User.objects.create_superuser(
            username='super_admin',
            password='password123',
            email='super@ui.ac.id'
        )

        self.barang_jual = Barang.objects.create(
            penjual=self.pemilik,
            nama='Kalkulator Casio FX-991EX',
            deskripsi='Kondisi sangat mulus dengan cover plastik',
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
            deskripsi='Catatan kuliah semester 1 lengkap',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            kondisi=Barang.LAYAK_PAKAI,
            harga=None,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('buku.jpg')
        )
        self.barang_pinjam = Barang.objects.create(
            penjual=self.pemilik,
            nama='Jas Lab Kimia',
            deskripsi='Jas lab ukuran L untuk praktikum',
            kategori=Barang.PAKAIAN,
            jenis=Barang.PINJAM,
            kondisi=Barang.BAIK,
            harga=None,
            status=Barang.DALAM_PROSES,
            foto=create_dummy_image('jas_lab.jpg')
        )

    def test_str_representation(self):
        """Memastikan metode __str__ mengembalikan format yang diharapkan."""
        expected = f'{self.barang_jual.nama} (Dijual) — {self.pemilik.username}'
        self.assertEqual(str(self.barang_jual), expected)

    def test_foto_url_property(self):
        """Memastikan properti foto_url mengembalikan URL atau string kosong."""
        self.assertTrue(self.barang_jual.foto_url.startswith('/media/'))

        barang_tanpa_foto = Barang(penjual=self.pemilik, nama='Barang Kosong', foto=None)
        self.assertEqual(barang_tanpa_foto.foto_url, '')

    def test_harga_display_variations(self):
        """Memastikan harga_display memformat harga jual atau mengembalikan 'Gratis'."""
        self.assertEqual(self.barang_jual.harga_display, 'Rp 150.000')
        self.assertEqual(self.barang_donasi.harga_display, 'Gratis')

        self.barang_jual.harga = 0
        self.assertEqual(self.barang_jual.harga_display, 'Gratis')

        self.barang_jual.harga = None
        self.assertEqual(self.barang_jual.harga_display, 'Gratis')

    def test_badge_color_class(self):
        """Memastikan badge_color_class mengembalikan class CSS yang tepat."""
        self.assertEqual(self.barang_jual.badge_color_class, 'badge-jual')
        self.assertEqual(self.barang_pinjam.badge_color_class, 'badge-pinjam')
        self.assertEqual(self.barang_donasi.badge_color_class, 'badge-donasi')

        self.barang_jual.jenis = 'unknown'
        self.assertEqual(self.barang_jual.badge_color_class, '')

    def test_status_color_class(self):
        """Memastikan status_color_class mengembalikan class CSS yang tepat."""
        self.assertEqual(self.barang_jual.status_color_class, 'status-tersedia')
        self.assertEqual(self.barang_pinjam.status_color_class, 'status-proses')

        self.barang_jual.status = Barang.SELESAI
        self.assertEqual(self.barang_jual.status_color_class, 'status-selesai')

        self.barang_jual.status = 'unknown'
        self.assertEqual(self.barang_jual.status_color_class, '')

    def test_permission_bisa_diedit_oleh(self):
        """Memastikan hak akses edit untuk seluruh variasi peran."""
        self.assertFalse(self.barang_jual.bisa_diedit_oleh(None))
        self.assertFalse(self.barang_jual.bisa_diedit_oleh(AnonymousUser()))
        self.assertFalse(self.barang_jual.bisa_diedit_oleh(self.pengguna_lain))
        self.assertTrue(self.barang_jual.bisa_diedit_oleh(self.pemilik))
        self.assertTrue(self.barang_jual.bisa_diedit_oleh(self.admin_user))
        self.assertTrue(self.barang_jual.bisa_diedit_oleh(self.super_user))

    def test_permission_bisa_dihapus_oleh(self):
        """Memastikan hak akses hapus untuk seluruh variasi peran."""
        self.assertFalse(self.barang_jual.bisa_dihapus_oleh(None))
        self.assertFalse(self.barang_jual.bisa_dihapus_oleh(AnonymousUser()))
        self.assertFalse(self.barang_jual.bisa_dihapus_oleh(self.pengguna_lain))
        self.assertTrue(self.barang_jual.bisa_dihapus_oleh(self.pemilik))
        self.assertTrue(self.barang_jual.bisa_dihapus_oleh(self.admin_user))
        self.assertTrue(self.barang_jual.bisa_dihapus_oleh(self.super_user))

    def test_queryset_tersedia(self):
        """Memastikan queryset tersedia() hanya mengambil barang berstatus TERSEDIA."""
        tersedia_qs = Barang.objects.tersedia()
        self.assertIn(self.barang_jual, tersedia_qs)
        self.assertIn(self.barang_donasi, tersedia_qs)
        self.assertNotIn(self.barang_pinjam, tersedia_qs)

    def test_queryset_filter_katalog(self):
        """Menguji pemfilteran kategori, jenis, pencarian q (nama/deskripsi), dan sorting."""
        qs = Barang.objects.all()

        # Filter kategori
        qs_kat = qs.filter_katalog(kategori=Barang.BUKU)
        self.assertEqual(qs_kat.count(), 1)
        self.assertEqual(qs_kat.first(), self.barang_donasi)

        # Filter jenis
        qs_jenis = qs.filter_katalog(jenis=Barang.DONASI)
        self.assertEqual(qs_jenis.count(), 1)
        self.assertEqual(qs_jenis.first(), self.barang_donasi)

        # Search query mencocokkan nama
        qs_search_nama = qs.filter_katalog(search_query='Kalkulator')
        self.assertEqual(qs_search_nama.count(), 1)
        self.assertEqual(qs_search_nama.first(), self.barang_jual)

        # Search query mencocokkan deskripsi
        qs_search_desc = qs.filter_katalog(search_query='semester 1')
        self.assertEqual(qs_search_desc.count(), 1)
        self.assertEqual(qs_search_desc.first(), self.barang_donasi)

        # Sort variations
        self.assertTrue(qs.filter_katalog(sort='-dibuat_pada').exists())
        self.assertTrue(qs.filter_katalog(sort='dibuat_pada').exists())
        self.assertTrue(qs.filter_katalog(sort='nama').exists())
        self.assertTrue(qs.filter_katalog(sort='harga').exists())
        self.assertTrue(qs.filter_katalog(sort='-harga').exists())
        self.assertTrue(qs.filter_katalog(sort='invalid_sort').exists())


class BarangFormTest(TestCase):
    """Pengujian Unit untuk Form Validasi BarangForm."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='user_form_tester',
            password='password123'
        )
        self.barang_existing = Barang.objects.create(
            penjual=self.user,
            nama='Barang Lama',
            kategori=Barang.ELEKTRONIK,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=50000,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('existing.jpg')
        )

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

    def test_form_valid_donasi_mengosongkan_harga(self):
        """Form mengosongkan harga (harga = None) otomatis jika jenisnya donasi."""
        data = {
            'nama': 'Novel Fiksi Ilmiah',
            'kategori': 'buku',
            'jenis': 'donasi',
            'kondisi': 'baik',
            'harga': 75000,
        }
        files = {'foto': create_dummy_image('novel.jpg')}
        form = BarangForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['harga'])

    def test_form_valid_pinjam_mengosongkan_harga(self):
        """Form mengosongkan harga (harga = None) otomatis jika jenisnya pinjam."""
        data = {
            'nama': 'Kabel HDMI 2 Meter',
            'kategori': 'elektronik',
            'jenis': 'pinjam',
            'kondisi': 'baik',
            'harga': 20000,
        }
        files = {'foto': create_dummy_image('kabel.jpg')}
        form = BarangForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['harga'])

    def test_form_invalid_foto_kosong_pada_create(self):
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

    def test_form_valid_foto_kosong_pada_edit_instance(self):
        """Form valid jika tidak mengunggah foto baru saat mengedit instance yang sudah ada fotonya."""
        data = {
            'nama': 'Barang Lama Diperbarui',
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baik',
            'harga': 60000,
        }
        form = BarangForm(data=data, files={}, instance=self.barang_existing)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_foto_ukuran_melebihi_5mb(self):
        """Form memicu ValidationError jika ukuran berkas foto > 5 MB."""
        oversized_file = create_dummy_image(
            filename='large.jpg',
            size_bytes=5 * 1024 * 1024 + 1024  # > 5 MB
        )
        data = {
            'nama': 'Monitor Gaming',
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baru',
            'harga': 1500000,
        }
        form = BarangForm(data=data, files={'foto': oversized_file})
        self.assertFalse(form.is_valid())
        self.assertIn('foto', form.errors)
        self.assertIn('5 MB', form.errors['foto'][0])

    def test_form_invalid_foto_bukan_gambar_valid(self):
        """Form memicu ValidationError jika berkas yang diunggah bukan gambar valid."""
        corrupt_file = create_dummy_image(filename='corrupt.jpg', is_valid_image=False)
        data = {
            'nama': 'Keyboard Rusak',
            'kategori': 'elektronik',
            'jenis': 'jual',
            'kondisi': 'baik',
            'harga': 50000,
        }
        form = BarangForm(data=data, files={'foto': corrupt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('foto', form.errors)
        self.assertTrue(
            any('bukan gambar yang valid' in err or 'valid image' in err.lower() for err in form.errors['foto'])
        )

    def test_clean_foto_corrupt_exception_directly(self):
        """Menguji clean_foto dengan berkas yang memicu exception Pillow saat verifikasi."""
        form = BarangForm()
        form.cleaned_data = {'foto': SimpleUploadedFile('dummy.jpg', b'corrupt_content')}
        with self.assertRaises(forms.ValidationError) as ctx:
            form.clean_foto()
        self.assertIn("Berkas yang diunggah bukan gambar yang valid.", str(ctx.exception))

    def test_clean_foto_empty_on_new_instance_directly(self):
        """Menguji clean_foto saat foto kosong pada instance baru."""
        form = BarangForm()
        form.cleaned_data = {'foto': None}
        with self.assertRaises(forms.ValidationError):
            form.clean_foto()

    def test_clean_foto_empty_on_existing_instance_returns_existing(self):
        """Menguji clean_foto saat foto kosong pada instance yang sudah ada."""
        form = BarangForm(instance=self.barang_existing)
        form.cleaned_data = {'foto': None}
        self.assertEqual(form.clean_foto(), self.barang_existing.foto)

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

    def test_form_invalid_harga_nol_atau_negatif_pada_jual(self):
        """Form invalid jika jenis jual memiliki harga <= 0 atau kosong."""
        for invalid_harga in [0, -1000, '']:
            form = BarangForm(
                data={
                    'nama': 'Keyboard Mekanikal',
                    'kategori': 'elektronik',
                    'jenis': 'jual',
                    'kondisi': 'baik',
                    'harga': invalid_harga,
                },
                files={'foto': create_dummy_image()}
            )
            self.assertFalse(form.is_valid())
            self.assertIn('harga', form.errors)


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
        self.superuser = User.objects.create_superuser(
            username='admin_super',
            password='password123',
            email='super@ui.ac.id'
        )

        self.barang = Barang.objects.create(
            penjual=self.pemilik,
            nama='Lampu Meja LED',
            deskripsi='Lampu meja belajar hemat energi',
            kategori=Barang.FURNITUR,
            jenis=Barang.JUAL,
            kondisi=Barang.BARU,
            harga=65000,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('lampu.jpg')
        )

    def test_show_katalog_anonymous_and_authenticated(self):
        """GET /katalog/ menghasilkan status 200 dan menguji visibilitas barang dalam_proses."""
        # Anonim
        res_anon = self.client.get('/katalog/')
        self.assertEqual(res_anon.status_code, 200)
        self.assertTemplateUsed(res_anon, 'katalog/katalog.html')

        # Buat barang status dalam_proses milik penjual
        barang_proses_pemilik = Barang.objects.create(
            penjual=self.pemilik,
            nama='Barang Proses Pemilik',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            status=Barang.DALAM_PROSES,
            foto=create_dummy_image('proses.jpg')
        )
        # Buat barang status dalam_proses milik pengguna lain
        barang_proses_lain = Barang.objects.create(
            penjual=self.pembeli,
            nama='Barang Proses Pembeli',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            status=Barang.DALAM_PROSES,
            foto=create_dummy_image('proses2.jpg')
        )

        # Login sebagai pemilik
        self.client.login(username='penjual_katalog', password='password123')
        res_auth = self.client.get('/katalog/')
        self.assertEqual(res_auth.status_code, 200)

        barang_list = res_auth.context['barang_list']
        self.assertIn(barang_proses_pemilik, barang_list)
        self.assertNotIn(barang_proses_lain, barang_list)

        # Filter query params
        res_filter = self.client.get('/katalog/?kategori=furnitur&jenis=jual&q=LED&sort=harga')
        self.assertEqual(res_filter.status_code, 200)

    def test_detail_barang_exists_and_404_uuid(self):
        """GET /katalog/<uuid:pk>/ 200 untuk barang ada dan 404 untuk UUID acak."""
        response = self.client.get(f'/katalog/{self.barang.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'katalog/detail_barang.html')

        random_id = uuid.uuid4()
        response_404 = self.client.get(f'/katalog/{random_id}/')
        self.assertEqual(response_404.status_code, 404)

    def test_detail_barang_minat_context(self):
        """Memastikan penentuan context sudah_berminat pada detail barang."""
        # Pengguna pembeli belum berminat
        self.client.login(username='calon_pembeli', password='password123')
        res_belum = self.client.get(f'/katalog/{self.barang.id}/')
        self.assertFalse(res_belum.context['sudah_berminat'])

        # Tandai minat
        MinatBarang.objects.create(barang=self.barang, pembeli=self.pembeli)
        res_sudah = self.client.get(f'/katalog/{self.barang.id}/')
        self.assertTrue(res_sudah.context['sudah_berminat'])

        # Pemilik melihat barangnya sendiri
        self.client.login(username='penjual_katalog', password='password123')
        res_pemilik = self.client.get(f'/katalog/{self.barang.id}/')
        self.assertFalse(res_pemilik.context['sudah_berminat'])

    def test_tambah_barang_view_flows(self):
        """Menguji view tambah_barang: unauthenticated, GET form, POST invalid, dan POST valid."""
        # Anonim -> redirect ke login
        res_anon = self.client.get('/katalog/tambah/')
        self.assertEqual(res_anon.status_code, 302)

        self.client.login(username='penjual_katalog', password='password123')

        # GET form
        res_get = self.client.get('/katalog/tambah/')
        self.assertEqual(res_get.status_code, 200)
        self.assertTemplateUsed(res_get, 'katalog/form_barang.html')
        self.assertEqual(res_get.context['mode'], 'tambah')

        # POST invalid
        res_post_inv = self.client.post('/katalog/tambah/', {'nama': ''})
        self.assertEqual(res_post_inv.status_code, 200)
        self.assertTrue(res_post_inv.context['form'].errors)

        # POST valid
        res_post_val = self.client.post('/katalog/tambah/', {
            'nama': 'Kursi Lipat Praktis',
            'kategori': 'furnitur',
            'jenis': 'jual',
            'kondisi': 'baik',
            'harga': 80000,
            'foto': create_dummy_image('kursi.jpg'),
        })
        self.assertEqual(res_post_val.status_code, 302)
        kursi = Barang.objects.get(nama='Kursi Lipat Praktis')
        self.assertEqual(kursi.penjual, self.pemilik)
        self.assertRedirects(res_post_val, f'/katalog/{kursi.id}/')

    def test_edit_barang_view_flows(self):
        """Menguji view edit_barang untuk anonim, user lain (403), pemilik, dan staff/superuser."""
        # Anonim -> 302
        res_anon = self.client.get(f'/katalog/{self.barang.id}/edit/')
        self.assertEqual(res_anon.status_code, 302)

        # Pengguna lain -> 403 Forbidden
        self.client.login(username='calon_pembeli', password='password123')
        res_403 = self.client.get(f'/katalog/{self.barang.id}/edit/')
        self.assertEqual(res_403.status_code, 403)

        # Pemilik GET
        self.client.login(username='penjual_katalog', password='password123')
        res_owner_get = self.client.get(f'/katalog/{self.barang.id}/edit/')
        self.assertEqual(res_owner_get.status_code, 200)
        self.assertEqual(res_owner_get.context['mode'], 'edit')

        # Pemilik POST invalid
        res_owner_inv = self.client.post(f'/katalog/{self.barang.id}/edit/', {
            'nama': '',
            'jenis': 'jual',
            'harga': 0,
        })
        self.assertEqual(res_owner_inv.status_code, 200)

        # Pemilik POST valid
        res_owner_val = self.client.post(f'/katalog/{self.barang.id}/edit/', {
            'nama': 'Lampu Meja LED Super Terang',
            'kategori': Barang.FURNITUR,
            'jenis': Barang.JUAL,
            'kondisi': Barang.BAIK,
            'harga': 70000,
        })
        self.assertEqual(res_owner_val.status_code, 302)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.nama, 'Lampu Meja LED Super Terang')

        # Staff GET & POST valid
        self.client.login(username='admin_moderator', password='password123')
        res_staff_get = self.client.get(f'/katalog/{self.barang.id}/edit/')
        self.assertEqual(res_staff_get.status_code, 200)

        res_staff_val = self.client.post(f'/katalog/{self.barang.id}/edit/', {
            'nama': 'Lampu Meja LED (Diedit Moderator)',
            'kategori': Barang.FURNITUR,
            'jenis': Barang.JUAL,
            'kondisi': Barang.BAIK,
            'harga': 60000,
        })
        self.assertEqual(res_staff_val.status_code, 302)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.nama, 'Lampu Meja LED (Diedit Moderator)')

        # Superuser POST valid
        self.client.login(username='admin_super', password='password123')
        res_super_val = self.client.post(f'/katalog/{self.barang.id}/edit/', {
            'nama': 'Lampu Meja LED Superuser',
            'kategori': Barang.FURNITUR,
            'jenis': Barang.JUAL,
            'kondisi': Barang.BAIK,
            'harga': 55000,
        })
        self.assertEqual(res_super_val.status_code, 302)

    def test_hapus_barang_view_flows(self):
        """Menguji view hapus_barang untuk anonim, user lain (403), GET 405, dan hapus berhasil."""
        # Anonim -> 302
        res_anon = self.client.post(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_anon.status_code, 302)

        # GET request -> 405 Method Not Allowed
        self.client.login(username='penjual_katalog', password='password123')
        res_get = self.client.get(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_get.status_code, 405)

        # Pengguna lain -> 403 Forbidden
        self.client.login(username='calon_pembeli', password='password123')
        res_403 = self.client.post(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_403.status_code, 403)

        # Staff hapus barang pengguna lain
        self.client.login(username='admin_moderator', password='password123')
        res_staff = self.client.post(f'/katalog/{self.barang.id}/hapus/')
        self.assertEqual(res_staff.status_code, 302)
        self.assertFalse(Barang.objects.filter(id=self.barang.id).exists())

        # Buat barang baru untuk pengujian hapus oleh pemilik
        barang_baru = Barang.objects.create(
            penjual=self.pemilik,
            nama='Barang Baru Dihapus',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('buku2.jpg')
        )
        self.client.login(username='penjual_katalog', password='password123')
        res_owner = self.client.post(f'/katalog/{barang_baru.id}/hapus/')
        self.assertEqual(res_owner.status_code, 302)
        self.assertFalse(Barang.objects.filter(id=barang_baru.id).exists())

        # Buat barang baru untuk pengujian hapus oleh superuser
        barang_super = Barang.objects.create(
            penjual=self.pemilik,
            nama='Barang Hapus Superuser',
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('buku3.jpg')
        )
        self.client.login(username='admin_super', password='password123')
        res_super = self.client.post(f'/katalog/{barang_super.id}/hapus/')
        self.assertEqual(res_super.status_code, 302)
        self.assertFalse(Barang.objects.filter(id=barang_super.id).exists())


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

    def test_tambah_barang_ajax_protection(self):
        """Endpoint tambah barang AJAX membutuhkan login dan hanya menerima method POST."""
        # Anonim -> 302
        res_anon = self.client.post('/katalog/tambah-ajax/', {})
        self.assertEqual(res_anon.status_code, 302)

        # GET method -> 405 Method Not Allowed
        self.client.login(username='ajax_tester', password='password123')
        res_get = self.client.get('/katalog/tambah-ajax/')
        self.assertEqual(res_get.status_code, 405)

    def test_tambah_barang_ajax_valid_status_201(self):
        """POST valid ke endpoint tambah barang AJAX mengembalikan JSON 201 dengan atribut barang."""
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
        """POST invalid ke endpoint tambah barang AJAX mengembalikan JSON 400 dengan daftar errors."""
        self.client.login(username='ajax_tester', password='password123')
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

    def test_katalog_json_format_and_filters(self):
        """GET /katalog/json/ mengembalikan daftar JSON beserta filter dan penanganan profile penjual."""
        # Respon dasar
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
        self.assertIn('penjual', first_item)
        self.assertEqual(first_item['nama'], 'Earphone Type-C')

        # Filter query params
        res_filter = self.client.get('/katalog/json/?kategori=elektronik&jenis=jual&q=Earphone&sort=harga')
        self.assertEqual(res_filter.status_code, 200)
        self.assertEqual(len(res_filter.json()), 1)

        # Penjual tanpa profile / profil fakultas kosong
        user_no_profile = User.objects.create_user(username='user_no_prof', password='password123')
        if hasattr(user_no_profile, 'profile'):
            user_no_profile.profile.delete()

        barang_no_foto = Barang.objects.create(
            penjual=user_no_profile,
            nama='Barang Tanpa Foto',
            kategori=Barang.LAINNYA,
            jenis=Barang.DONASI,
            status=Barang.TERSEDIA,
            foto=create_dummy_image('dummy.jpg')
        )
        # Kosongkan foto pada level DB
        Barang.objects.filter(id=barang_no_foto.id).update(foto='')

        res_edge = self.client.get('/katalog/json/?q=Tanpa+Foto')
        self.assertEqual(res_edge.status_code, 200)
        items = res_edge.json()
        self.assertEqual(len(items), 1)
        self.assertIsNone(items[0]['foto_url'])
        self.assertEqual(items[0]['penjual']['username'], 'user_no_prof')
