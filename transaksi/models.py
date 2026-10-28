import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from katalog.models import Barang


class Transaksi(models.Model):
    MENUNGGU = 'menunggu'
    DISETUJUI = 'disetujui'
    DITOLAK = 'ditolak'
    SELESAI = 'selesai'
    DIBATALKAN = 'dibatalkan'

    STATUS_CHOICES = [
        (MENUNGGU, 'Menunggu Persetujuan Penjual'),
        (DISETUJUI, 'Disetujui, Dalam Proses Serah Terima'),
        (DITOLAK, 'Ditolak oleh Penjual'),
        (SELESAI, 'Selesai'),
        (DIBATALKAN, 'Dibatalkan'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    barang = models.ForeignKey(Barang, on_delete=models.CASCADE, related_name='transaksi')
    pembeli = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transaksi_sebagai_pembeli')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=MENUNGGU)
    catatan_pembeli = models.TextField(blank=True, help_text='Pesan atau catatan dari pembeli kepada penjual.')
    dibuat_pada = models.DateTimeField(default=timezone.now)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-dibuat_pada']
        constraints = [
            models.UniqueConstraint(
                fields=['barang', 'pembeli'],
                condition=models.Q(status='menunggu') | models.Q(status='disetujui'),
                name='unique_transaksi_aktif_per_pembeli',
            ),
        ]

    def __str__(self):
        return f'Transaksi {self.barang.nama} oleh {self.pembeli.username}'

    @property
    def penjual(self):
        return self.barang.penjual

    @property
    def is_aktif(self):
        return self.status in (self.MENUNGGU, self.DISETUJUI)

    @property
    def is_selesai(self):
        return self.status == self.SELESAI

    def bisa_disetujui_oleh(self, user):
        return self.status == self.MENUNGGU and self.barang.penjual == user

    def bisa_ditolak_oleh(self, user):
        return self.status == self.MENUNGGU and self.barang.penjual == user

    def bisa_diselesaikan_oleh(self, user):
        return self.status == self.DISETUJUI and self.barang.penjual == user

    def bisa_dibatalkan_oleh(self, user):
        return self.status in (self.MENUNGGU, self.DISETUJUI) and (
            self.pembeli == user or self.barang.penjual == user
        )