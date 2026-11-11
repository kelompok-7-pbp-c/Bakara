import uuid

from django.test import TestCase, override_settings
from django.urls import reverse
from authentication.models import User
from katalog.models import Barang
from transaksi.models import Transaksi
from review.models import Review

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

    # MODEL PERMISSIONS
    def test_transaksi_status_permissions(self):
        self.assertFalse(self.transaksi.bisa_disetujui_oleh(self.pembeli))
        self.assertFalse(self.transaksi.bisa_ditolak_oleh(self.pembeli))

        self.transaksi.status = Transaksi.DISETUJUI
        self.assertTrue(self.transaksi.bisa_diselesaikan_oleh(self.penjual))
        self.assertFalse(self.transaksi.bisa_diselesaikan_oleh(self.pembeli))
        self.assertTrue(self.transaksi.bisa_dibatalkan_oleh(self.penjual))

        self.transaksi.status = Transaksi.SELESAI
        self.assertFalse(self.transaksi.bisa_dibatalkan_oleh(self.penjual))

    # CREATE
    def test_create_transaction_success(self):
        self.transaksi.status = Transaksi.DIBATALKAN
        self.transaksi.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[self.barang.id]),
            {"catatan_pembeli": "  Tolong hubungi saya dulu.  "},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.assertEqual(Transaksi.objects.count(), 2)
        transaksi_baru = Transaksi.objects.exclude(pk=self.transaksi.pk).get()
        self.assertEqual(transaksi_baru.pembeli, self.pembeli)
        self.assertEqual(transaksi_baru.barang, self.barang)
        self.assertEqual(transaksi_baru.status, Transaksi.MENUNGGU)
        self.assertEqual(transaksi_baru.catatan_pembeli, "Tolong hubungi saya dulu.")

    def test_create_transaction_rejects_own_item(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[self.barang.id]),
            {"catatan_pembeli": "Saya pemiliknya."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("katalog:detail_barang", args=[self.barang.id]),
        )
        self.assertEqual(Transaksi.objects.count(), 1)

    def test_create_transaction_rejects_unavailable_item(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[self.barang.id]),
            {"catatan_pembeli": "Saya masih berminat."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("katalog:detail_barang", args=[self.barang.id]),
        )
        self.assertEqual(Transaksi.objects.count(), 1)

    def test_create_transaction_rejects_duplicate_active_request(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[self.barang.id]),
            {"catatan_pembeli": "Pengajuan kedua."},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.assertEqual(Transaksi.objects.count(), 1)

    def test_create_transaction_not_found(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[uuid.uuid4()]),
            {"catatan_pembeli": "Barang tidak ditemukan."},
        )

        self.assertEqual(response.status_code, 404)

    def test_create_transaction_requires_post(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(
            reverse("transaksi:create_transaction", args=[self.barang.id])
        )

        self.assertEqual(response.status_code, 405)

    def test_create_transaction_login_required(self):
        response = self.client.post(
            reverse("transaksi:create_transaction", args=[self.barang.id]),
            {"catatan_pembeli": "Belum login."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertEqual(Transaksi.objects.count(), 1)

    # UPDATE STATUS
    def test_update_transaction_status_approve(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DISETUJUI)
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_update_transaction_status_approve_rejected_when_item_unavailable(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_update_transaction_status_approve_rejected_if_another_is_approved(self):
        pembeli_lain = User.objects.create_user(
            username="pembeli_lain_test",
            password="password123",
            email="pembeli.lain@ui.ac.id",
        )
        Transaksi.objects.create(
            barang=self.barang,
            pembeli=pembeli_lain,
            status=Transaksi.DISETUJUI,
        )
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_update_transaction_status_complete(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "selesai"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.SELESAI)
        self.assertEqual(self.barang.status, Barang.SELESAI)

    def test_update_transaction_status_reject(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "tolak"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DITOLAK)
        self.assertEqual(self.barang.status, Barang.TERSEDIA)

    def test_update_transaction_status_reject_keeps_item_in_process_if_another_is_approved(self):
        pembeli_lain = User.objects.create_user(
            username="pembeli_lain_test",
            password="password123",
            email="pembeli.lain@ui.ac.id",
        )
        Transaksi.objects.create(
            barang=self.barang,
            pembeli=pembeli_lain,
            status=Transaksi.DISETUJUI,
        )
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "tolak"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DITOLAK)
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_update_transaction_status_reject_keeps_completed_item(self):
        self.barang.status = Barang.SELESAI
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "tolak"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DITOLAK)
        self.assertEqual(self.barang.status, Barang.SELESAI)

    def test_update_transaction_status_rejects_invalid_action(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "aksi_tidak_valid"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)

    def test_update_transaction_status_rejects_action_not_allowed_by_status(self):
        self.transaksi.status = Transaksi.DITOLAK
        self.transaksi.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DITOLAK)

    def test_update_transaction_status_forbidden_for_non_seller(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertEqual(response.status_code, 403)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)

    def test_update_transaction_status_not_found(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[uuid.uuid4()]),
            {"aksi": "setujui"},
        )

        self.assertEqual(response.status_code, 404)

    def test_update_transaction_status_requires_post(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id])
        )

        self.assertEqual(response.status_code, 405)

    def test_update_transaction_status_login_required(self):
        response = self.client.post(
            reverse("transaksi:update_transaction_status", args=[self.transaksi.id]),
            {"aksi": "setujui"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    # CANCEL
    def test_cancel_transaction_by_buyer(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)
        self.assertEqual(self.barang.status, Barang.TERSEDIA)

    def test_cancel_approved_transaction_by_seller_returns_item_to_available(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)
        self.assertEqual(self.barang.status, Barang.TERSEDIA)

    def test_cancel_approved_transaction_keeps_completed_item(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()
        self.barang.status = Barang.SELESAI
        self.barang.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertRedirects(response, reverse("transaksi:show_transaction"))
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)
        self.assertEqual(self.barang.status, Barang.SELESAI)

    def test_cancel_transaction_forbidden_for_unrelated_user(self):
        orang_lain = User.objects.create_user(
            username="orang_lain_test",
            password="password123",
            email="orang.lain@ui.ac.id",
        )
        self.client.force_login(orang_lain)
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertEqual(response.status_code, 403)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)

    def test_cancel_transaction_not_found(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[uuid.uuid4()])
        )

        self.assertEqual(response.status_code, 404)

    def test_cancel_transaction_requires_post(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertEqual(response.status_code, 405)

    def test_cancel_transaction_login_required(self):
        response = self.client.post(
            reverse("transaksi:cancel_transaction", args=[self.transaksi.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    # JSON VARIATIONS
    def test_get_transaction_json_as_seller(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        item = data["transaksi"][0]
        self.assertTrue(item["is_penjual"])
        self.assertEqual(item["partner_role"], "Penerima Donasi")
        self.assertEqual(item["partner_name"], "pembeli_test")

    def test_get_transaction_json_jual_with_profile_and_review(self):
        self.barang.jenis = Barang.JUAL
        self.barang.harga = 12500
        self.barang.save()
        profile = self.penjual.profile
        profile.full_name = "Penjual Buku"
        profile.whatsapp = "08123456789"
        profile.line_id = "penjual_line"
        profile.save()
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi.",
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))

        self.assertEqual(response.status_code, 200)
        item = response.json()["transaksi"][0]
        self.assertFalse(item["is_penjual"])
        self.assertEqual(item["barang_jenis_label"], "Jual")
        self.assertEqual(item["barang_harga"], "Rp 12.500")
        self.assertEqual(item["partner_role"], "Penjual")
        self.assertEqual(item["partner_name"], "Penjual Buku")
        self.assertEqual(item["partner_wa"], "https://wa.me/628123456789")
        self.assertEqual(item["partner_line"], "penjual_line")
        self.assertTrue(item["sudah_diulas"])

        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))
        item = response.json()["transaksi"][0]
        self.assertTrue(item["is_penjual"])
        self.assertEqual(item["partner_role"], "Pembeli")
        self.assertTrue(item["sudah_diulas"])

    def test_get_transaction_json_pinjam_roles(self):
        self.barang.jenis = Barang.PINJAM
        self.barang.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))
        item = response.json()["transaksi"][0]
        self.assertEqual(item["barang_jenis_label"], "Pinjam")
        self.assertEqual(item["barang_harga"], "Dipinjamkan")
        self.assertEqual(item["partner_role"], "Pemilik Barang")

        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))
        item = response.json()["transaksi"][0]
        self.assertEqual(item["partner_role"], "Peminjam")

    def test_get_transaction_json_uses_username_without_partner_profile(self):
        self.penjual.profile.delete()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))

        self.assertEqual(response.status_code, 200)
        item = response.json()["transaksi"][0]
        self.assertEqual(item["partner_name"], "penjual_test")
        self.assertEqual(item["partner_wa"], "")
        self.assertEqual(item["partner_line"], "")

    def test_get_transaction_json_without_photo(self):
        self.barang.foto = ""
        self.barang.save(update_fields=["foto"])

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("transaksi:get_transaction_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transaksi"][0]["barang_foto"], "")

    def test_get_transaction_json_handles_photo_without_url(self):
        self.client.login(username="pembeli_test", password="password123")

        with override_settings(MEDIA_URL=None):
            response = self.client.get(reverse("transaksi:get_transaction_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transaksi"][0]["barang_foto"], "")
