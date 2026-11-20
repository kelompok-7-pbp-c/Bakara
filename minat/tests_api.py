import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Profile
from katalog.models import Barang
from minat.models import MinatBarang
from transaksi.models import Transaksi


User = get_user_model()


class MinatAPITest(APITestCase):
    def setUp(self):
        self.penjual = User.objects.create_user(username='penjual_api', password='password-api')
        self.pembeli = User.objects.create_user(username='pembeli_api', password='password-api')
        self.lain = User.objects.create_user(username='lain_api', password='password-api')
        Profile.objects.create(user=self.penjual, full_name='Nama Penjual', whatsapp='08123456789', line_id='penjual-line')
        Profile.objects.create(user=self.pembeli, full_name='Nama Pembeli', whatsapp='08111111111', line_id='pembeli-line')
        self.barang = Barang.objects.create(
            penjual=self.penjual, nama='Buku API', kategori=Barang.BUKU,
            jenis=Barang.JUAL, kondisi=Barang.BAIK, harga=25000, foto='buku.jpg',
        )
        self.list_url = reverse('minat_api:minat-list')

    def test_requires_login_and_scopes_list_to_participants(self):
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN)
        minat = MinatBarang.objects.create(barang=self.barang, pembeli=self.pembeli)
        self.client.force_authenticate(self.lain)
        self.assertEqual(self.client.get(self.list_url).data['total'], 0)
        self.client.force_authenticate(self.pembeli)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['minat'][0]['id'], str(minat.pk))
        self.assertEqual(response.data['minat'][0]['nama_kontak'], 'Nama Penjual')
        self.assertEqual(response.data['minat'][0]['whatsapp_link'], 'https://wa.me/628123456789')

    def test_create_interest_validates_ownership_availability_and_limit(self):
        self.client.force_authenticate(self.pembeli)
        response = self.client.post(self.list_url, {'barang': str(self.barang.pk)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post(self.list_url, {'barang': str(self.barang.pk)}, format='json')
        self.assertEqual(duplicate.status_code, status.HTTP_200_OK)
        self.assertEqual(MinatBarang.objects.count(), 1)

        self.client.force_authenticate(self.penjual)
        own = self.client.post(self.list_url, {'barang': str(self.barang.pk)}, format='json')
        self.assertEqual(own.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.pembeli)
        barang_lain = []
        for index in range(3):
            barang_lain.append(Barang.objects.create(
                penjual=self.penjual, nama=f'Barang {index}', kategori=Barang.BUKU,
                jenis=Barang.JUAL, kondisi=Barang.BAIK, harga=1000, foto='barang.jpg',
            ))
        for barang in barang_lain[:2]:
            MinatBarang.objects.create(barang=barang, pembeli=self.pembeli)
        limited = self.client.post(self.list_url, {'barang': str(barang_lain[2].pk)}, format='json')
        self.assertEqual(limited.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_is_limited_to_the_interested_buyer(self):
        minat = MinatBarang.objects.create(barang=self.barang, pembeli=self.pembeli)
        detail = reverse('minat_api:minat-detail', args=[minat.pk])
        self.client.force_authenticate(self.lain)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.pembeli)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MinatBarang.objects.filter(pk=minat.pk).exists())

    def test_seller_can_process_interest_into_transaction(self):
        minat = MinatBarang.objects.create(barang=self.barang, pembeli=self.pembeli)
        action = reverse('minat_api:minat-proses-transaksi', args=[minat.pk])
        self.client.force_authenticate(self.lain)
        self.assertEqual(self.client.post(action).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.penjual)
        response = self.client.post(action)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaksi = Transaksi.objects.get(pk=response.data['transaksi'])
        self.assertEqual(transaksi.pembeli, self.pembeli)
        self.assertEqual(transaksi.status, Transaksi.DISETUJUI)
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.status, Barang.DALAM_PROSES)
        self.assertEqual(self.client.post(action).status_code, status.HTTP_409_CONFLICT)

    def test_missing_minat_and_wrong_method(self):
        self.client.force_authenticate(self.pembeli)
        detail = reverse('minat_api:minat-detail', args=[uuid.uuid4()])
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
