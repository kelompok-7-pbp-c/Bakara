import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Barang(models.Model):
    """
    Model utama untuk listing barang di platform Bakara.
    Setiap barang dimiliki oleh satu User (penjual/pemberi).
    """

    # Pilihan Jenis Transaksi 
    JUAL    = 'jual'
    PINJAM  = 'pinjam'
    DONASI  = 'donasi'
    JENIS_CHOICES = [
        (JUAL,   'Dijual'),
        (PINJAM, 'Dipinjamkan'),
        (DONASI, 'Didonasikan'),
    ]

    # Pilihan Kategori 
    BUKU         = 'buku'
    ELEKTRONIK   = 'elektronik'
    PAKAIAN      = 'pakaian'
    FURNITUR     = 'furnitur'
    ALAT_TULIS   = 'alat_tulis'
    KEBUTUHAN_KOS= 'kebutuhan_kos'
    OLAHRAGA     = 'olahraga'
    LAINNYA      = 'lainnya'
    KATEGORI_CHOICES = [
        (BUKU,          'Buku & Alat Belajar'),
        (ELEKTRONIK,    'Elektronik & Gadget'),
        (PAKAIAN,       'Pakaian & Aksesoris'),
        (FURNITUR,      'Furnitur & Dekorasi'),
        (ALAT_TULIS,    'Alat Tulis & Kantor'),
        (KEBUTUHAN_KOS, 'Kebutuhan Kos'),
        (OLAHRAGA,      'Olahraga & Hobi'),
        (LAINNYA,       'Lainnya'),
    ]

    # Pilihan Kondisi Barang 
    BARU             = 'baru'
    BAIK             = 'baik'
    LAYAK_PAKAI      = 'layak_pakai'
    KONDISI_CHOICES = [
        (BARU,        'Baru / Belum Dipakai'),
        (BAIK,        'Baik (sedikit bekas)'),
        (LAYAK_PAKAI, 'Layak Pakai (bekas, tapi oke)'),
    ]

    # Pilihan Status Listing 
    TERSEDIA      = 'tersedia'
    DALAM_PROSES  = 'dalam_proses'
    SELESAI       = 'selesai'
    STATUS_CHOICES = [
        (TERSEDIA,     'Tersedia'),
        (DALAM_PROSES, 'Dalam Proses'),
        (SELESAI,      'Selesai / Sudah Diambil'),
    ]

    # Fields 
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='ID unik barang (UUID).',
    )
    penjual = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='barang_listing',
        verbose_name='Penjual / Pemberi',
    )

    # Info utama
    nama        = models.CharField('Nama Barang', max_length=120)
    deskripsi   = models.TextField('Deskripsi', blank=True)
    kategori    = models.CharField('Kategori', max_length=20, choices=KATEGORI_CHOICES, default=LAINNYA)
    jenis       = models.CharField('Jenis Transaksi', max_length=10, choices=JENIS_CHOICES, default=JUAL)
    kondisi     = models.CharField('Kondisi', max_length=15, choices=KONDISI_CHOICES, default=BAIK)
    status      = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default=TERSEDIA)

    # Harga (null/0 = gratis untuk jenis donasi/pinjam)
    harga = models.PositiveIntegerField(
        'Harga (Rp)',
        null=True,
        blank=True,
        help_text='Kosongkan jika gratis atau untuk barang yang dipinjamkan/didonasikan.',
    )

    # Lokasi pengambilan (masih berupa teks saja, nanti mungkin bisa diintegrasikan ke OpenStreetMap API)
    lokasi = models.CharField(
        'Lokasi Pengambilan',
        max_length=100,
        blank=True,
        help_text='Contoh: Asrama UI, Fakultas Teknik, dll.',
    )

    # Foto barang (opsional — URL eksternal)
    foto_url = models.URLField(
        'URL Foto Barang',
        blank=True,
        help_text='Link foto barang (opsional).',
    )

    # Timestamps
    dibuat_pada   = models.DateTimeField('Dibuat Pada', default=timezone.now)
    diperbarui_pada = models.DateTimeField('Diperbarui Pada', auto_now=True)

    class Meta:
        db_table    = 'katalog_barang'
        ordering    = ['-dibuat_pada']
        verbose_name        = 'Barang'
        verbose_name_plural = 'Daftar Barang'

    def __str__(self):
        return f'{self.nama} ({self.get_jenis_display()}) — {self.penjual.username}'

    @property
    def harga_display(self):
        """Tampilkan harga dalam format Rupiah, atau 'Gratis' jika null/0."""
        if not self.harga:
            return 'Gratis'
        return f'Rp {self.harga:,}'.replace(',', '.')

    @property
    def badge_color_class(self):
        """CSS class untuk badge warna berdasarkan jenis transaksi."""
        return {
            self.JUAL:   'badge-jual',
            self.PINJAM: 'badge-pinjam',
            self.DONASI: 'badge-donasi',
        }.get(self.jenis, '')

    @property
    def status_color_class(self):
        """CSS class untuk badge warna berdasarkan status."""
        return {
            self.TERSEDIA:     'status-tersedia',
            self.DALAM_PROSES: 'status-proses',
            self.SELESAI:      'status-selesai',
        }.get(self.status, '')
