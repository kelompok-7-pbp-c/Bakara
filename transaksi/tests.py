from django.test import TestCase
from django.urls import reverse
from authentication.models import User
from katalog.models import Barang
from transaksi.models import Transaksi

class TransaksiTest(TestCase):
    def setUp(self):
        self.penjual = User.objects.create_user(
            username="penjual_test",
            password="password123",
            email="penjual@ui.ac.id",
        )
        self.pembeli = User.objects.create_user(
            username="pembeli_test",
            password="password123",
            email="pembeli@ui.ac.id",
        )

        self.barang = Barang.objects.create(
            penjual=self.penjual,
            nama="Buku Struktur Data",
            deskripsi="Buku materi kuliah Fasilkom UI masih bagus.",
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            kondisi=Barang.BAIK,
            status=Barang.TERSEDIA,
            lokasi="Fasilkom UI",
            foto="test.jpg",
        )

        self.transaksi = Transaksi.objects.create(
            barang=self.barang,
            pembeli=self.pembeli,
            status=Transaksi.MENUNGGU,
            catatan_pembeli="Bisa ambil di kutek jam 12?",
        )

    # URL
    def test_transaksi_url_is_accessible(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:show_transaction"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transaksi.html")

    def test_transaksi_url_login_required(self):
        response = self.client.get(reverse("transaksi:show_transaction"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")
        self.assertEqual(response.status_code, 404)

    # MODEL
    def test_transaksi_model(self):
        expected_str = f"Transaksi {self.barang.nama} oleh {self.pembeli.username}"
        self.assertEqual(str(self.transaksi), expected_str)
        self.assertEqual(self.transaksi.penjual, self.penjual)
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)
        self.assertTrue(self.transaksi.is_aktif)
        self.assertFalse(self.transaksi.is_selesai)
        self.assertTrue(self.transaksi.bisa_disetujui_oleh(self.penjual))
        self.assertTrue(self.transaksi.bisa_ditolak_oleh(self.penjual))
        self.assertTrue(self.transaksi.bisa_dibatalkan_oleh(self.pembeli))

    # TEMPLATE
    def test_transaksi_page(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:show_transaction"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transaksi.html")
        self.assertContains(response, "Transaksi Saya")
        self.assertContains(response, "Riwayat dan Status")
        self.assertContains(response, "Permintaan Saya")
        self.assertContains(response, "Barang Saya")

    def test_empty_transaksi_page(self):
        Transaksi.objects.all().delete()
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:show_transaction"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belum ada riwayat transaksi yang ditemukan.")

    # STATUS CHANGE
    def test_completed_transaksi(self):
        self.transaksi.status = Transaksi.SELESAI
        self.transaksi.save()
        self.assertTrue(self.transaksi.is_selesai)
        self.assertFalse(self.transaksi.is_aktif)

    def test_cancelled_transaksi(self):
        self.transaksi.status = Transaksi.DIBATALKAN
        self.transaksi.save()
        self.assertFalse(self.transaksi.is_aktif)
        self.assertFalse(self.transaksi.is_selesai)

    # JSON
    def test_get_transaction_json(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("transaksi", data)
        self.assertEqual(data["total"], 1)

        item = data["transaksi"][0]
        self.assertEqual(item["barang_nama"], "Buku Struktur Data")
        self.assertEqual(item["barang_jenis"], "donasi")
        self.assertEqual(item["status"], "menunggu")
        self.assertFalse(item["is_penjual"])

    def test_get_transaction_json_login_required(self):
        response = self.client.get(reverse("transaksi:get_transaction_json"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)