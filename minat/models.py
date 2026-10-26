from django.db import models
from django.conf import settings
from django.db import models

from katalog.models import Barang
from django.utils import timezone


class MinatBarang(models.Model):
    barang = models.ForeignKey(
        Barang,
        on_delete=models.CASCADE,
        related_name='minat',
    )
    pembeli = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='minat_barang',
    )

    class Meta:
        db_table = 'minat_barang'
        constraints = [
            models.UniqueConstraint(
                fields=['barang', 'pembeli'],
                name='unique_minat_per_pembeli_barang',
            ),
        ]

    def __str__(self):
        return f'{self.pembeli.username} tertarik pada {self.barang.nama}'


class Transaksi(models.Model):
    MENUNGGU = 'menunggu'
    SELESAI = 'selesai'
    DIBATALKAN = 'dibatalkan'
    STATUS_CHOICES = [
        (MENUNGGU, 'Menunggu serah terima'),
        (SELESAI, 'Selesai'),
        (DIBATALKAN, 'Dibatalkan'),
    ]

    minat = models.ForeignKey(
        MinatBarang, on_delete=models.PROTECT, related_name='transaksi'
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=MENUNGGU)
    dibuat_pada = models.DateTimeField(default=timezone.now)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transaksi'
        ordering = ['-dibuat_pada']
        constraints = [
            models.UniqueConstraint(
                fields=['minat'], condition=models.Q(status='menunggu'),
                name='unique_active_transaction_per_interest',
            ),
        ]

    @property
    def barang(self):
        return self.minat.barang

    @property
    def pembeli(self):
        return self.minat.pembeli

    def __str__(self):
        return f'Transaksi {self.barang.nama} — {self.get_status_display()}'
