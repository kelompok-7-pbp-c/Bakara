import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model untuk platform Bakara.
    Mewarisi seluruh field AbstractUser (username, email, is_staff, dll.)
    dengan mengganti primary key menjadi UUID untuk keamanan.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='ID unik pengguna (UUID).',
    )

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Daftar Pengguna'

    def __str__(self):
        return self.username


class Profile(models.Model):
    """
    Profil tambahan Mahasiswa yang terhubung OneToOne dengan User.
    Dibuat otomatis via signal saat User baru terdaftar.
    """

    FACULTY_CHOICES = [
        ('FK', 'Fakultas Kedokteran'),
        ('FKG', 'Fakultas Kedokteran Gigi'),
        ('FMIPA', 'Fakultas Matematika dan Ilmu Pengetahuan Alam'),
        ('FT', 'Fakultas Teknik'),
        ('FH', 'Fakultas Hukum'),
        ('FEB', 'Fakultas Ekonomi dan Bisnis'),
        ('FIB', 'Fakultas Ilmu Pengetahuan Budaya'),
        ('FPSI', 'Fakultas Psikologi'),
        ('FISIP', 'Fakultas Ilmu Sosial dan Ilmu Politik'),
        ('FKM', 'Fakultas Kesehatan Masyarakat'),
        ('FASILKOM', 'Fakultas Ilmu Komputer'),
        ('FIK', 'Fakultas Ilmu Keperawatan'),
        ('FF', 'Fakultas Farmasi'),
        ('FIA', 'Fakultas Ilmu Administrasi'),
        ('VOKASI', 'Program Pendidikan Vokasi'),
        ('SIL', 'Sekolah Ilmu Lingkungan'),
        ('SKSG', 'Sekolah Kajian Stratejik dan Global'),
    ]

    user = models.OneToOneField(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Akun Pengguna',
    )
    full_name = models.CharField('Nama lengkap', max_length=100, blank=True)
    faculty = models.CharField(
        'Fakultas', max_length=10, choices=FACULTY_CHOICES, blank=True
    )
    angkatan = models.PositiveSmallIntegerField('Angkatan', null=True, blank=True)
    whatsapp = models.CharField('Nomor WhatsApp', max_length=15, blank=True)
    line_id = models.CharField('ID LINE', max_length=20, blank=True)
    photo = models.ImageField('Foto profil', upload_to='profile_photos/', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        verbose_name = 'Profil Pengguna'
        verbose_name_plural = 'Daftar Profil'

    def __str__(self):
        return f'Profil {self.user.username}'

    @property
    def is_complete(self):
        """Memeriksa apakah seluruh informasi profil wajib telah terisi."""
        return all((
            self.full_name,
            self.faculty,
            self.angkatan,
            self.whatsapp,
            self.line_id,
            self.photo,
        ))

    @property
    def whatsapp_link(self):
        """Menghasilkan tautan wa.me dengan kode negara Indonesia (+62)."""
        if not self.whatsapp:
            return ''
        return f'https://wa.me/62{self.whatsapp[1:]}'
