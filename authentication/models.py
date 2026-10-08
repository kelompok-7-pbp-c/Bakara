from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Kosong boleh di database karena profil dibuat otomatis saat pertama diakses;
    # kewajiban mengisi dicek di ProfileForm.
    full_name = models.CharField('Nama lengkap', max_length=100, blank=True)
    faculty = models.CharField('Fakultas', max_length=10, choices=FACULTY_CHOICES, blank=True)
    angkatan = models.PositiveSmallIntegerField('Angkatan', null=True, blank=True)
    whatsapp = models.CharField('Nomor WhatsApp', max_length=15, blank=True)
    line_id = models.CharField('ID LINE', max_length=20, blank=True)
    photo = models.ImageField('Foto profil', upload_to='profile_photos/', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return f'Profil {self.user.username}'

    @property
    def is_complete(self):
        return all((
            self.full_name, self.faculty, self.angkatan,
            self.whatsapp, self.line_id, self.photo,
        ))

    @property
    def whatsapp_link(self):
        # wa.me butuh format internasional tanpa '+', misal 6281234567890
        return f'https://wa.me/62{self.whatsapp[1:]}' if self.whatsapp else ''
