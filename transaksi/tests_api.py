import uuid

from django.test import TestCase
from django.urls import reverse

from authentication.models import User
from katalog.models import Barang
from transaksi.models import Transaksi
from review.models import Review


class TransaksiAPITestCase(TestCase):
    """Base setUp yang dipakai semua test API transaksi."""

    def setUp(self):
        self.penjual = User.objects.create_user(
            username='penjual_api',
            password='password123',
            email='penjual_api@ui.ac.id',
        )
        self.pembeli = User.objects.create_user(
            username='pembeli_api',
            password='password123',
            email='pembeli_api@ui.ac.id',
        )
        self.orang_lain = User.objects.create_user(
            username='orang_lain_api',
            password='password123',
            email='orang_lain_api@ui.ac.id',
        )
        self.barang = Barang.objects.create(
            penjual=self.penjual,
            nama='Buku Kalkulus',
            deskripsi='Buku kalkulus bekas.',
            kategori=Barang.BUKU,
            jenis=Barang.JUAL,
            kondisi=Barang.BAIK,
            status=Barang.TERSEDIA,
            harga=50000,
            lokasi='Fasilkom UI',
            foto='test.jpg',
        )
        self.transaksi = Transaksi.objects.create(
            barang=self.barang,
            pembeli=self.pembeli,
            status=Transaksi.MENUNGGU,
            catatan_pembeli='Bisa COD di kampus?',
        )

    # -------------------------------------------------------------------
    # LIST endpoint
    # -------------------------------------------------------------------

    def test_list_requires_login(self):
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_list_as_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('transaksi', data)
        self.assertEqual(data['total'], 1)
        item = data['transaksi'][0]
        self.assertFalse(item['is_penjual'])
        self.assertEqual(item['status'], Transaksi.MENUNGGU)

    def test_list_as_penjual(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)
        item = data['transaksi'][0]
        self.assertTrue(item['is_penjual'])

    def test_list_filter_by_status(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url, {'status': Transaksi.DITOLAK})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 0)

    def test_list_filter_by_peran_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url, {'peran': 'pembeli'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 1)

    def test_list_filter_by_peran_penjual_returns_empty_for_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.get(url, {'peran': 'penjual'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 0)

    # -------------------------------------------------------------------
    # POST (buat transaksi baru)
    # -------------------------------------------------------------------

    def test_create_transaction_success(self):
        self.transaksi.status = Transaksi.DIBATALKAN
        self.transaksi.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.post(url, {
            'barang': str(self.barang.id),
            'catatan_pembeli': 'Pengajuan baru.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Transaksi.objects.filter(status=Transaksi.MENUNGGU).count(), 1)

    def test_create_transaction_rejects_own_item(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.post(url, {
            'barang': str(self.barang.id),
            'catatan_pembeli': 'Saya pemiliknya.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_transaction_rejects_unavailable_item(self):
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.post(url, {
            'barang': str(self.barang.id),
            'catatan_pembeli': 'Masih mau.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_transaction_rejects_duplicate_active(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.post(url, {
            'barang': str(self.barang.id),
            'catatan_pembeli': 'Duplikat.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_transaction_requires_login(self):
        url = reverse('transaksi_api:transaksi-list')
        response = self.client.post(url, {
            'barang': str(self.barang.id),
        }, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    # -------------------------------------------------------------------
    # DETAIL endpoint
    # -------------------------------------------------------------------

    def test_detail_as_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], str(self.transaksi.id))

    def test_detail_as_penjual(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_forbidden_for_unrelated_user(self):
        self.client.login(username='orang_lain_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_detail_not_found(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[uuid.uuid4()])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detail_requires_login(self):
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # -------------------------------------------------------------------
    # DELETE (batalkan via detail endpoint)
    # -------------------------------------------------------------------

    def test_delete_cancels_transaction_by_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)

    def test_delete_cancels_approved_transaction_and_restores_barang(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)
        self.assertEqual(self.barang.status, Barang.TERSEDIA)

    def test_delete_forbidden_for_completed_transaction(self):
        self.transaksi.status = Transaksi.SELESAI
        self.transaksi.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

    # -------------------------------------------------------------------
    # AKSI endpoint
    # -------------------------------------------------------------------

    def test_aksi_setujui_by_penjual(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'setujui'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DISETUJUI)
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)

    def test_aksi_setujui_forbidden_for_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'setujui'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)

    def test_aksi_setujui_rejected_when_another_is_approved(self):
        pembeli_lain = User.objects.create_user(
            username='pembeli_lain_api',
            password='password123',
            email='pembeli.lain@ui.ac.id',
        )
        Transaksi.objects.create(
            barang=self.barang,
            pembeli=pembeli_lain,
            status=Transaksi.DISETUJUI,
        )
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'setujui'}, content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.MENUNGGU)

    def test_aksi_tolak_by_penjual(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'tolak'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DITOLAK)

    def test_aksi_tolak_forbidden_for_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'tolak'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_aksi_selesai_by_penjual(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()
        self.barang.status = Barang.DALAM_PROSES
        self.barang.save()

        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'selesai'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.barang.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.SELESAI)
        self.assertEqual(self.barang.status, Barang.SELESAI)

    def test_aksi_selesai_forbidden_for_pembeli(self):
        self.transaksi.status = Transaksi.DISETUJUI
        self.transaksi.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'selesai'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_aksi_batalkan_by_pembeli(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'batalkan'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)

    def test_aksi_batalkan_by_penjual(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'batalkan'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, Transaksi.DIBATALKAN)

    def test_aksi_batalkan_selesai_rejected(self):
        self.transaksi.status = Transaksi.SELESAI
        self.transaksi.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'batalkan'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_aksi_invalid(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'aksi_tidak_ada'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_aksi_forbidden_for_unrelated_user(self):
        self.client.login(username='orang_lain_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'batalkan'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_aksi_requires_login(self):
        url = reverse('transaksi_api:transaksi-aksi', args=[self.transaksi.id])
        response = self.client.post(url, {'aksi': 'batalkan'}, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_aksi_not_found(self):
        self.client.login(username='penjual_api', password='password123')
        url = reverse('transaksi_api:transaksi-aksi', args=[uuid.uuid4()])
        response = self.client.post(url, {'aksi': 'setujui'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------
    # Serializer field checks
    # -------------------------------------------------------------------

    def test_serializer_fields_lengkap(self):
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        data = response.json()

        expected_fields = [
            'id', 'barang', 'barang_nama', 'barang_jenis', 'barang_jenis_label',
            'barang_harga_display', 'barang_lokasi', 'barang_foto_url',
            'pembeli', 'pembeli_username', 'penjual_id', 'penjual_username',
            'status', 'status_display', 'catatan_pembeli',
            'dibuat_pada', 'dibuat_pada_display', 'diperbarui_pada',
            'is_penjual', 'partner_role', 'partner_name',
            'partner_wa', 'partner_line', 'sudah_diulas',
            'bisa_disetujui', 'bisa_ditolak', 'bisa_diselesaikan', 'bisa_dibatalkan',
        ]
        for field in expected_fields:
            self.assertIn(field, data, msg=f'Field "{field}" tidak ada di response.')

    def test_sudah_diulas_true_when_review_exists(self):
        Review.objects.create(
            transaksi=self.transaksi,
            reviewer=self.pembeli,
            reviewee=self.penjual,
            rating=5,
            komentar='Mantap!',
        )
        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertTrue(response.json()['sudah_diulas'])

    def test_partner_role_donasi(self):
        self.barang.jenis = Barang.DONASI
        self.barang.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.json()['partner_role'], 'Donatur')

    def test_partner_role_pinjam_as_pembeli(self):
        self.barang.jenis = Barang.PINJAM
        self.barang.save()

        self.client.login(username='pembeli_api', password='password123')
        url = reverse('transaksi_api:transaksi-detail', args=[self.transaksi.id])
        response = self.client.get(url)
        self.assertEqual(response.json()['partner_role'], 'Pemilik Barang')
