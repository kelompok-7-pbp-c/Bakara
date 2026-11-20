import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from authentication.models import User
from katalog.models import Barang
from review.models import Review
from transaksi.models import Transaksi


class ReviewAPITest(APITestCase):
    def setUp(self):
        self.penjual = User.objects.create_user(
            username="penjual_test",
            password="test-password",
            email="penjual@example.com",
        )
        self.pembeli = User.objects.create_user(
            username="pembeli_test",
            password="test-password",
            email="pembeli@example.com",
        )
        self.pengunjung = User.objects.create_user(
            username="pengunjung_test",
            password="test-password",
            email="pengunjung@example.com",
        )

        self.barang_ulasan = Barang.objects.create(
            penjual=self.penjual,
            nama="Buku Basis Data",
            deskripsi="Buku kuliah edisi revisi.",
            kategori=Barang.BUKU,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            status=Barang.SELESAI,
            harga=75000,
            lokasi="Fasilkom UI",
            foto="buku.jpg",
        )
        self.transaksi_diulas = Transaksi.objects.create(
            barang=self.barang_ulasan,
            pembeli=self.pembeli,
            status=Transaksi.SELESAI,
            catatan_pembeli="COD di kampus.",
        )
        self.review = Review.objects.create(
            transaksi=self.transaksi_diulas,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar="Barang sesuai deskripsi.",
        )

        self.barang_baru = Barang.objects.create(
            penjual=self.penjual,
            nama="Keyboard Mechanical",
            deskripsi="Kondisi terawat.",
            kategori=Barang.ELEKTRONIK,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            status=Barang.SELESAI,
            harga=150000,
            lokasi="Perpus Pusat UI",
            foto="keyboard.jpg",
        )
        self.transaksi_baru = Transaksi.objects.create(
            barang=self.barang_baru,
            pembeli=self.pembeli,
            status=Transaksi.SELESAI,
            catatan_pembeli="Ambil sore hari.",
        )

        self.list_url = reverse("review_api:review-list")
        self.detail_url = reverse("review_api:review-detail", args=[self.review.id])
        self.payload = {
            "transaksi": str(self.transaksi_baru.id),
            "rating": 4,
            "komentar": "Pengiriman cepat dan aman.",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.review.id))
        self.assertEqual(response.data[0]["rating"], 5)

        detail_response = self.client.get(self.detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["id"], str(self.review.id))

    def test_filter_list_and_missing_review(self):
        response = self.client.get(self.list_url, {"rating": "5"})
        self.assertEqual(len(response.data), 1)

        empty_response = self.client.get(self.list_url, {"rating": "1"})
        self.assertEqual(empty_response.data, [])

        missing_url = reverse("review_api:review-detail", args=[uuid.uuid4()])
        self.assertEqual(
            self.client.get(missing_url).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_guest_and_unrelated_user_cannot_write(self):
        for user in (None, self.pengunjung, self.penjual):
            self.client.force_authenticate(user=user)
            self.assertEqual(
                self.client.post(self.list_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.patch(
                    self.detail_url, {"komentar": "Ubah"}, format="json"
                ).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )

    def test_reviewer_can_create_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.pembeli)

        create_res = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_res.data["reviewer"], self.pembeli.id)
        self.assertEqual(create_res.data["reviewee"], self.penjual.id)

        patch_res = self.client.patch(
            self.detail_url, {"komentar": "Komentar baru."}, format="json"
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["komentar"], "Komentar baru.")

        put_res = self.client.put(
            self.detail_url,
            {
                "transaksi": str(self.transaksi_diulas.id),
                "rating": 5,
                "komentar": "Update penuh.",
            },
            format="json",
        )
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)

        del_res = self.client.delete(self.detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(del_res.content, b"")
        self.assertFalse(Review.objects.filter(pk=self.review.id).exists())

    def test_validation_errors(self):
        self.client.force_authenticate(user=self.pembeli)

        bad_rating = self.client.post(
            self.list_url,
            {**self.payload, "rating": 99},
            format="json",
        )
        self.assertEqual(bad_rating.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rating", bad_rating.data)

        duplicate = self.client.post(
            self.list_url,
            {
                "transaksi": str(self.transaksi_diulas.id),
                "rating": 5,
                "komentar": "Duplikat.",
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.pembeli)
        self.assertEqual(
            self.client.delete(self.list_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_session_write_without_and_with_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(
            client.login(username="pembeli_test", password="test-password")
        )

        no_csrf = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(no_csrf.status_code, status.HTTP_403_FORBIDDEN)

        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value

        with_csrf = client.post(
            self.list_url,
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(with_csrf.status_code, status.HTTP_201_CREATED)