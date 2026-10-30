import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from transaksi.models import Transaksi


class Review(models.Model):
    RATING_CHOICES = [(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_diberikan')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_diterima')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    komentar = models.TextField(blank=True, help_text='Kesan atau pesan untuk pihak yang diulas.')
    dibuat_pada = models.DateTimeField(default=timezone.now)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-dibuat_pada']
        constraints = [
            models.UniqueConstraint(
                fields=['transaksi', 'reviewer'],
                name='unique_review_per_pihak_transaksi',
            ),
        ]

    def __str__(self):
        return f'Review {self.rating}/5 dari {self.reviewer.username} untuk {self.reviewee.username}'

    def bisa_diedit_oleh(self, user):
        return self.reviewer == user

    def bisa_dihapus_oleh(self, user):
        return self.reviewer == user