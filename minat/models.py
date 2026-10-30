import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone

from katalog.models import Barang


class MinatBarang(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    dibuat_pada = models.DateTimeField(default=timezone.now)

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
