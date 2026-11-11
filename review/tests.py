from django.test import TestCase
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from authentication.models import User
from katalog.models import Barang
from transaksi.models import Transaksi
from review.models import Review


class ReviewTest(TestCase):
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
        self.orang_lain = User.objects.create_user(
            username="orang_lain_test",
            password="password123",
            email="orang.lain@ui.ac.id",
        )

        self.barang = Barang.objects.create(
            penjual=self.penjual,
            nama="Buku Struktur Data",
            deskripsi="Buku materi kuliah Fasilkom UI masih bagus.",
            kategori=Barang.BUKU,
            jenis=Barang.DONASI,
            kondisi=Barang.BAIK,
            status=Barang.SELESAI,
            lokasi="Fasilkom UI",
            foto="test.jpg",
        )

        self.transaksi = Transaksi.objects.create(
            barang=self.barang,
            pembeli=self.pembeli,
            status=Transaksi.SELESAI,
            catatan_pembeli="Bisa ambil di kutek jam 12?",
        )

    # URL
    def test_review_url_is_accessible(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:show_review"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "review.html")

    def test_review_url_login_required(self):
        response = self.client.get(reverse("review:show_review"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_review_json_login_required(self):
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    # MODEL
    def test_review_model(self):
        review = Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi dan penjual ramah.",
        )
        expected_str = f"Review 5/5 dari {self.pembeli.username} untuk {self.penjual.username}"
        self.assertEqual(str(review), expected_str)
        self.assertEqual(review.transaksi, self.transaksi)
        self.assertEqual(review.reviewer, self.pembeli)
        self.assertEqual(review.reviewee, self.penjual)
        self.assertEqual(review.rating, 5)
        self.assertTrue(review.bisa_diedit_oleh(self.pembeli))
        self.assertTrue(review.bisa_dihapus_oleh(self.pembeli))
        self.assertFalse(review.bisa_diedit_oleh(self.penjual))
        self.assertFalse(review.bisa_dihapus_oleh(self.penjual))

    def test_review_unique_per_pihak(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    transaksi=self.transaksi,
                    reviewer=self.pembeli,
                    reviewee=self.penjual,
                    rating=3,
                )
        self.assertEqual(Review.objects.count(), 1)

    def test_both_parties_can_review_same_transaksi(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.penjual,
            reviewee=self.pembeli,
            rating=4,
        )
        self.assertEqual(Review.objects.filter(transaksi=self.transaksi).count(), 2)

    # TEMPLATE
    def test_review_page(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:show_review"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "review.html")
        self.assertContains(response, "Ringkasan Rating")
        self.assertContains(response, "Tulis Ulasan")
        self.assertContains(response, "Diterima")
        self.assertContains(response, "Diberikan")
        self.assertContains(response, "Menunggu")

    # CREATE
    def test_create_review_by_buyer(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 5, "komentar": "Barang bagus dan penjual tepat waktu."},
        )
        self.assertRedirects(response, reverse("review:show_review"))
        self.assertEqual(Review.objects.count(), 1)

        review = Review.objects.first()
        self.assertEqual(review.transaksi, self.transaksi)
        self.assertEqual(review.reviewer, self.pembeli)
        self.assertEqual(review.reviewee, self.penjual)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.komentar, "Barang bagus dan penjual tepat waktu.")

    def test_create_review_by_seller_is_rejected(self):
        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 4, "komentar": "Penjual mencoba mengulas diri sendiri."},
            follow=True,
        )
        # Pastikan gagal tersimpan karena penjual dilarang mengulas
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_requires_completed_transaksi(self):
        self.transaksi.status = Transaksi.MENUNGGU
        self.transaksi.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 5, "komentar": "Belum selesai tapi mau diulas."},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ulasan hanya bisa dibuat setelah transaksi selesai.")
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_duplicate_is_rejected(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Ulasan pertama.",
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 1, "komentar": "Ulasan kedua."},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kamu sudah memberi ulasan untuk transaksi ini.")
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.first().komentar, "Ulasan pertama.")

    def test_create_review_forbidden_for_other_user(self):
        self.client.login(username="orang_lain_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 5, "komentar": "Aku bukan pihak transaksi ini."},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_login_required(self):
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 5, "komentar": "Belum login."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_get_not_allowed(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(
            reverse("review:create_review", args=[self.transaksi.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_create_review_invalid_rating(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 9, "komentar": "Rating di luar rentang."},
        )
        self.assertRedirects(response, reverse("review:show_review"))
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_without_rating(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"komentar": "Lupa memilih bintang."},
        )
        self.assertRedirects(response, reverse("review:show_review"))
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_comment_too_long(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[self.transaksi.id]),
            {"rating": 5, "komentar": "a" * 501},
        )
        self.assertRedirects(response, reverse("review:show_review"))
        self.assertEqual(Review.objects.count(), 0)

    def test_create_review_nonexistent_transaksi_returns_404(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:create_review", args=[uuid.uuid4()]),
            {"rating": 5, "komentar": "Transaksi tidak ada."},
        )
        self.assertEqual(response.status_code, 404)

    # EDIT
    def test_edit_review(self):
        review = Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi.",
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:edit_review", args=[review.id]),
            {"rating": 3, "komentar": "Ternyata ada yang lecet."},
        )
        self.assertRedirects(response, reverse("review:show_review"))

        review.refresh_from_db()
        self.assertEqual(review.rating, 3)
        self.assertEqual(review.komentar, "Ternyata ada yang lecet.")

    def test_edit_review_forbidden_for_non_owner(self):
        review = Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi.",
        )

        self.client.login(username="penjual_test", password="password123")
        response = self.client.post(
            reverse("review:edit_review", args=[review.id]),
            {"rating": 1, "komentar": "Penerima ulasan mencoba mengubah."},
        )
        self.assertEqual(response.status_code, 403)

        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.komentar, "Barang sesuai deskripsi.")

    # DELETE
    def test_delete_review(self):
        review = Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.post(
            reverse("review:delete_review", args=[review.id])
        )
        self.assertRedirects(response, reverse("review:show_review"))
        self.assertEqual(Review.objects.count(), 0)

    def test_delete_review_forbidden_for_non_owner(self):
        review = Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )

        self.client.login(username="orang_lain_test", password="password123")
        response = self.client.post(
            reverse("review:delete_review", args=[review.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Review.objects.count(), 1)

    # JSON
    def test_get_review_json_diterima(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi.",
        )

        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ringkasan", data)
        self.assertEqual(len(data["diterima"]), 1)
        self.assertEqual(len(data["diberikan"]), 0)
        self.assertEqual(data["ringkasan"]["total"], 1)
        self.assertEqual(data["ringkasan"]["rata_rata"], 5.0)
        self.assertEqual(data["ringkasan"]["sebaran"]["5"], 1)

        item = data["diterima"][0]
        self.assertEqual(item["barang_nama"], "Buku Struktur Data")
        self.assertEqual(item["pihak_nama"], "pembeli_test")
        self.assertEqual(item["rating"], 5)
        self.assertEqual(item["komentar"], "Barang sesuai deskripsi.")
        self.assertEqual(item["transaksi_id"], str(self.transaksi.id))

    def test_get_review_json_diberikan(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=4,
            komentar="Penjual ramah.",
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["diberikan"]), 1)
        self.assertEqual(len(data["diterima"]), 0)
        self.assertEqual(data["ringkasan"]["total"], 0)
        self.assertEqual(data["ringkasan"]["rata_rata"], 0)

        item = data["diberikan"][0]
        self.assertEqual(item["pihak_nama"], "penjual_test")
        self.assertEqual(item["rating"], 4)

    def test_get_review_json_menunggu(self):
        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["menunggu"]), 1)

        item = data["menunggu"][0]
        self.assertEqual(item["transaksi_id"], str(self.transaksi.id))
        self.assertEqual(item["barang_nama"], "Buku Struktur Data")
        self.assertEqual(item["pihak_nama"], "penjual_test")

    def test_get_review_json_menunggu_empty_if_not_completed(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["menunggu"]), 0)

    def test_get_review_json_menunggu_removed_after_reviewed(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )

        self.client.login(username="pembeli_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["menunggu"]), 0)

        # Penjual tidak memiliki tab menunggu ulasan, jadi jumlahnya 0
        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(len(response.json()["menunggu"]), 0)
\
    def test_get_review_json_average_and_distribution(self):
        pembeli_kedua = User.objects.create_user(
            username="pembeli_kedua",
            password="password123",
            email="pembeli.kedua@ui.ac.id",
        )
        transaksi_kedua = Transaksi.objects.create(
            barang=self.barang,
            pembeli=pembeli_kedua,
            status=Transaksi.SELESAI,
        )

        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
        )
        Review.objects.create(
            transaksi=transaksi_kedua,
            reviewer=pembeli_kedua,
            reviewee=self.penjual,
            rating=4,
        )

        self.client.login(username="penjual_test", password="password123")
        response = self.client.get(reverse("review:get_review_json"))
        self.assertEqual(response.status_code, 200)
        ringkasan = response.json()["ringkasan"]
        self.assertEqual(ringkasan["total"], 2)
        self.assertEqual(ringkasan["rata_rata"], 4.5)
        self.assertEqual(ringkasan["sebaran"]["5"], 1)
        self.assertEqual(ringkasan["sebaran"]["4"], 1)
        self.assertEqual(ringkasan["sebaran"]["1"], 0)

