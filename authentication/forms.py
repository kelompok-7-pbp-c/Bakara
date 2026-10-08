import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from authentication.models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email UI',
        help_text='Gunakan email @ui.ac.id kamu.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not email.endswith('@ui.ac.id'):
            raise forms.ValidationError('Email harus menggunakan domain @ui.ac.id.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email ini sudah terdaftar.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username atau Email')

    def clean(self):
        # Izinkan login pakai email: ubah email menjadi username sebelum autentikasi
        identifier = self.cleaned_data.get('username', '')
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                self.cleaned_data['username'] = user.username
        return super().clean()


class ProfileForm(forms.ModelForm):
    MIN_ANGKATAN = 1950
    MAX_PHOTO_SIZE = 2 * 1024 * 1024  # 2 MB
    PHOTO_FORMATS = ('JPEG', 'PNG', 'WEBP')

    # Lebih longgar dari model supaya input seperti '+62 812-3456-7890' bisa dirapikan dulu
    whatsapp = forms.CharField(
        label='Nomor WhatsApp',
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Contoh: 081234567890', 'inputmode': 'tel'}),
    )

    class Meta:
        model = Profile
        fields = ('photo', 'full_name', 'faculty', 'angkatan', 'whatsapp', 'line_id')
        widgets = {
            'angkatan': forms.NumberInput(attrs={'placeholder': 'Contoh: 2023'}),
            'line_id': forms.TextInput(attrs={'placeholder': 'Contoh: kesya.clara'}),
            # FileInput (bukan ClearableFileInput) supaya tidak ada opsi menghapus foto
            'photo': forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
        }
        help_texts = {
            'photo': 'Format JPG, PNG, atau WEBP. Maksimal 2 MB.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Di model boleh kosong, tapi saat mengisi profil semua field wajib
        for field in self.fields.values():
            field.required = True
        self.fields['faculty'].choices = [('', 'Pilih fakultas')] + Profile.FACULTY_CHOICES

    def clean_full_name(self):
        full_name = ' '.join(self.cleaned_data['full_name'].split())
        if len(full_name) < 2:
            raise forms.ValidationError('Nama lengkap terlalu pendek.')
        return full_name

    def clean_angkatan(self):
        angkatan = self.cleaned_data['angkatan']
        current_year = timezone.now().year
        if not self.MIN_ANGKATAN <= angkatan <= current_year:
            raise forms.ValidationError(
                f'Angkatan harus antara {self.MIN_ANGKATAN} dan {current_year}.'
            )
        return angkatan

    def clean_whatsapp(self):
        number = re.sub(r'[\s-]', '', self.cleaned_data['whatsapp'])
        # Terima 08xx, 628xx, atau +628xx lalu simpan dalam format 08xx
        match = re.fullmatch(r'(?:\+?62|0)(8\d{7,12})', number)
        if not match:
            raise forms.ValidationError('Nomor WhatsApp tidak valid. Contoh: 081234567890.')
        return '0' + match.group(1)

    def clean_line_id(self):
        line_id = self.cleaned_data['line_id'].strip().lower()
        if not re.fullmatch(r'[a-z0-9._-]{4,20}', line_id):
            raise forms.ValidationError(
                'ID LINE harus 4–20 karakter dan hanya berisi huruf, angka, titik, '
                'tanda hubung, atau garis bawah.'
            )
        return line_id

    def clean_photo(self):
        photo = self.cleaned_data['photo']
        # Foto lama yang tidak diganti tidak perlu dicek ulang
        if photo and photo != self.instance.photo:
            if photo.size > self.MAX_PHOTO_SIZE:
                raise forms.ValidationError('Ukuran foto maksimal 2 MB.')
            if photo.image.format not in self.PHOTO_FORMATS:
                raise forms.ValidationError('Foto harus berformat JPG, PNG, atau WEBP.')
        return photo
