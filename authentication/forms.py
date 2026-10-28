import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

from authentication.models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email UI',
        help_text='Gunakan email @ui.ac.id kamu.',
    )

    class Meta:
        # Menggunakan get_user_model() di dalam Meta menghindari import
        # langsung yang bisa menyebabkan circular import saat app startup.
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not email.endswith('@ui.ac.id'):
            raise forms.ValidationError(
                'Email harus menggunakan domain @ui.ac.id.'
            )
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email ini sudah terdaftar.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username atau Email')

    def clean(self):
        identifier = self.cleaned_data.get('username', '')
        if '@' in identifier:
            User = get_user_model()
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                self.cleaned_data['username'] = user.username
        return super().clean()


class ProfileForm(forms.ModelForm): 
    MIN_ANGKATAN = 1950
    MAX_PHOTO_SIZE = 2 * 1024 * 1024  # 2 MB
    PHOTO_FORMATS = ('JPEG', 'PNG', 'WEBP')

    # Override field whatsapp agar menerima format yang lebih fleksibel
    # sebelum dinormalisasi di clean_whatsapp().
    whatsapp = forms.CharField(
        label='Nomor WhatsApp',
        max_length=20,
        widget=forms.TextInput(
            attrs={'placeholder': 'Contoh: 081234567890', 'inputmode': 'tel'}
        ),
    )

    class Meta:
        model = Profile
        fields = ('photo', 'full_name', 'faculty', 'angkatan', 'whatsapp', 'line_id')
        widgets = {
            'angkatan': forms.NumberInput(attrs={'placeholder': 'Contoh: 2023'}),
            'line_id': forms.TextInput(attrs={'placeholder': 'Contoh: kesya.clara'}),
            # FileInput (bukan ClearableFileInput) agar tidak ada opsi hapus foto.
            'photo': forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
        }
        help_texts = {
            'photo': 'Format JPG, PNG, atau WEBP. Maksimal 2 MB.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field wajib untuk transaksi mahasiswa UI
        required_fields = ('full_name', 'faculty', 'angkatan', 'whatsapp')
        for field_name in required_fields:
            self.fields[field_name].required = True
        
        # Field opsional
        self.fields['line_id'].required = False
        self.fields['photo'].required = False
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
        # Hapus spasi dan tanda hubung, lalu normalisasi ke format 08xx.
        number = re.sub(r'[\s-]', '', self.cleaned_data['whatsapp'])
        match = re.fullmatch(r'(?:\+?62|0)(8\d{7,12})', number)
        if not match:
            raise forms.ValidationError(
                'Nomor WhatsApp tidak valid. Contoh: 081234567890.'
            )
        return '0' + match.group(1)

    def clean_line_id(self):
        # Validasi ID LINE hanya jika pengguna mengisinya.
        line_id = self.cleaned_data.get('line_id', '').strip().lower()
        if not line_id:
            return ''  # Boleh kosong jika tidak punya LINE
        if not re.fullmatch(r'[a-z0-9._-]{4,20}', line_id):
            raise forms.ValidationError(
                'ID LINE harus 4–20 karakter dan hanya berisi huruf, angka, '
                'titik, tanda hubung, atau garis bawah.'
            )
        return line_id
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        # Foto lama yang tidak diganti tidak perlu dicek ulang.
        if photo and photo != self.instance.photo:
            if photo.size > self.MAX_PHOTO_SIZE:
                raise forms.ValidationError('Ukuran foto maksimal 2 MB.')
            if photo.image.format not in self.PHOTO_FORMATS:
                raise forms.ValidationError('Foto harus berformat JPG, PNG, atau WEBP.')
        return photo