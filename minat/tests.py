from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from katalog.models import Barang
from minat.models import MinatBarang
from transaksi.models import Transaksi


User = get_user_model()


class MinatViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.penjual = User.objects.create_user(
            username='penjual', password='password-kuat-123'
        )
        cls.pembeli = User.objects.create_user(
            username='pembeli', password='password-kuat-123'
        )
        cls.pembeli_lain = User.objects.create_user(
            username='pembeli-lain', password='password-kuat-123'
        )
        cls.barang = Barang.objects.create(
            penjual=cls.penjual,
            nama='Buku Django',
            kategori=Barang.BUKU,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=50000,
            foto='barang_photos/buku.jpg',
        )

    def test_tandai_minat_memerlukan_login(self):
        response = self.client.post(
            reverse('minat:tandai_minat', args=[self.barang.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)
        self.assertFalse(MinatBarang.objects.exists())

    def test_tandai_minat_hanya_menerima_post(self):
        self.client.force_login(self.pembeli)

        response = self.client.get(
            reverse('minat:tandai_minat', args=[self.barang.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertFalse(MinatBarang.objects.exists())

    def test_pembeli_bisa_menandai_minat(self):
        self.client.force_login(self.pembeli)

        response = self.client.post(
            reverse('minat:tandai_minat', args=[self.barang.pk])
        )

        self.assertRedirects(
            response,
            reverse('katalog:detail_barang', args=[self.barang.pk]),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            MinatBarang.objects.filter(
                barang=self.barang, pembeli=self.pembeli
            ).exists()
        )

    def test_menandai_minat_berulang_tidak_membuat_duplikat(self):
        self.client.force_login(self.pembeli)
        url = reverse('minat:tandai_minat', args=[self.barang.pk])

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            MinatBarang.objects.filter(
                barang=self.barang, pembeli=self.pembeli
            ).count(),
            1,
        )

    def test_penjual_tidak_bisa_menandai_minat_barang_sendiri(self):
        self.client.force_login(self.penjual)

        self.client.post(
            reverse('minat:tandai_minat', args=[self.barang.pk])
        )

        self.assertFalse(MinatBarang.objects.exists())

    def test_barang_tidak_tersedia_tidak_bisa_diminati(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save(update_fields=['status'])
        self.client.force_login(self.pembeli)

        self.client.post(
            reverse('minat:tandai_minat', args=[self.barang.pk])
        )

        self.assertFalse(MinatBarang.objects.exists())

    def test_pembeli_bisa_membatalkan_minatnya(self):
        minat = MinatBarang.objects.create(
            barang=self.barang, pembeli=self.pembeli
        )
        self.client.force_login(self.pembeli)

        response = self.client.post(
            reverse('minat:batalkan_minat', args=[self.barang.pk])
        )

        self.assertRedirects(
            response,
            reverse('katalog:detail_barang', args=[self.barang.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(MinatBarang.objects.filter(pk=minat.pk).exists())

    def test_pengguna_tidak_bisa_membatalkan_minat_orang_lain(self):
        minat = MinatBarang.objects.create(
            barang=self.barang, pembeli=self.pembeli
        )
        self.client.force_login(self.pembeli_lain)

        self.client.post(
            reverse('minat:batalkan_minat', args=[self.barang.pk])
        )

        self.assertTrue(MinatBarang.objects.filter(pk=minat.pk).exists())

    def test_daftar_peminat_menampilkan_minat_pembeli_dan_penjual(self):
        minat = MinatBarang.objects.create(
            barang=self.barang, pembeli=self.pembeli
        )

        self.client.force_login(self.pembeli)
        response = self.client.get(reverse('minat:daftar_peminat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['minat_saya']), [minat])

        self.client.force_login(self.penjual)
        response = self.client.get(reverse('minat:daftar_peminat'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['peminat_barang_saya']), [minat])

    def test_daftar_peminat_menyembunyikan_minat_dengan_transaksi_selesai(self):
        minat = MinatBarang.objects.create(
            barang=self.barang, pembeli=self.pembeli
        )
        Transaksi.objects.create(
            barang=self.barang,
            pembeli=self.pembeli,
            status=Transaksi.SELESAI,
        )
        self.client.force_login(self.pembeli)

        response = self.client.get(reverse('minat:daftar_peminat'))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(minat, response.context['minat_saya'])

    def test_daftar_peminat_memerlukan_login(self):
        response = self.client.get(reverse('minat:daftar_peminat'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)


class ProsesTransaksiDariMinatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.penjual = User.objects.create_user(
            username='penjual', password='password-kuat-123'
        )
        cls.pembeli = User.objects.create_user(
            username='pembeli', password='password-kuat-123'
        )
        cls.pengguna_lain = User.objects.create_user(
            username='pengguna-lain', password='password-kuat-123'
        )
        cls.barang = Barang.objects.create(
            penjual=cls.penjual,
            nama='Kursi Belajar',
            kategori=Barang.FURNITUR,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            harga=100000,
            foto='barang_photos/kursi.jpg',
        )
        cls.minat = MinatBarang.objects.create(
            barang=cls.barang, pembeli=cls.pembeli
        )

    def test_penjual_memproses_minat_membuat_transaksi_dan_mengubah_status(self):
        self.client.force_login(self.penjual)

        response = self.client.post(
            reverse('minat:proses_transaksi', args=[self.minat.pk])
        )

        self.assertRedirects(
            response,
            reverse('transaksi:show_transaction'),
            fetch_redirect_response=False,
        )
        transaksi = Transaksi.objects.get(barang=self.barang)
        self.assertEqual(transaksi.pembeli, self.pembeli)
        self.assertEqual(transaksi.status, Transaksi.DISETUJUI)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_pengguna_yang_bukan_penjual_tidak_bisa_memproses_minat(self):
        self.client.force_login(self.pengguna_lain)

        response = self.client.post(
            reverse('minat:proses_transaksi', args=[self.minat.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Transaksi.objects.exists())

    def test_barang_yang_sudah_diproses_tidak_membuat_transaksi(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save(update_fields=['status'])
        self.client.force_login(self.penjual)

        self.client.post(
            reverse('minat:proses_transaksi', args=[self.minat.pk])
        )

        self.assertFalse(Transaksi.objects.exists())

    def test_transaksi_aktif_yang_sudah_ada_mencegah_transaksi_baru(self):
        Transaksi.objects.create(
            barang=self.barang,
            pembeli=self.pengguna_lain,
            status=Transaksi.MENUNGGU,
        )
        self.client.force_login(self.penjual)

        self.client.post(
            reverse('minat:proses_transaksi', args=[self.minat.pk])
        )

        self.assertEqual(Transaksi.objects.filter(barang=self.barang).count(), 1)
        self.assertFalse(
            Transaksi.objects.filter(
                barang=self.barang, pembeli=self.pembeli
            ).exists()
        )
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.status, Barang.TERSEDIA)

    def test_memproses_minat_hanya_menerima_post(self):
        self.client.force_login(self.penjual)

        response = self.client.get(
            reverse('minat:proses_transaksi', args=[self.minat.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertFalse(Transaksi.objects.exists())
