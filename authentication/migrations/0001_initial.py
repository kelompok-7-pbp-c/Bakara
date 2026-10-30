import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='ID unik pengguna (UUID).', primary_key=True, serialize=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Pengguna',
                'verbose_name_plural': 'Daftar Pengguna',
                'db_table': 'auth_users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(blank=True, max_length=100, verbose_name='Nama lengkap')),
                ('faculty', models.CharField(blank=True, choices=[('FK', 'Fakultas Kedokteran'), ('FKG', 'Fakultas Kedokteran Gigi'), ('FMIPA', 'Fakultas Matematika dan Ilmu Pengetahuan Alam'), ('FT', 'Fakultas Teknik'), ('FH', 'Fakultas Hukum'), ('FEB', 'Fakultas Ekonomi dan Bisnis'), ('FIB', 'Fakultas Ilmu Pengetahuan Budaya'), ('FPSI', 'Fakultas Psikologi'), ('FISIP', 'Fakultas Ilmu Sosial dan Ilmu Politik'), ('FKM', 'Fakultas Kesehatan Masyarakat'), ('FASILKOM', 'Fakultas Ilmu Komputer'), ('FIK', 'Fakultas Ilmu Keperawatan'), ('FF', 'Fakultas Farmasi'), ('FIA', 'Fakultas Ilmu Administrasi'), ('VOKASI', 'Program Pendidikan Vokasi'), ('SIL', 'Sekolah Ilmu Lingkungan'), ('SKSG', 'Sekolah Kajian Stratejik dan Global')], max_length=10, verbose_name='Fakultas')),
                ('angkatan', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Angkatan')),
                ('whatsapp', models.CharField(blank=True, max_length=15, verbose_name='Nomor WhatsApp')),
                ('line_id', models.CharField(blank=True, max_length=20, verbose_name='ID LINE')),
                ('photo', models.ImageField(blank=True, upload_to='profile_photos/', verbose_name='Foto profil')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Akun Pengguna')),
            ],
            options={
                'verbose_name': 'Profil Pengguna',
                'verbose_name_plural': 'Daftar Profil',
                'db_table': 'profiles',
            },
        ),
    ]
