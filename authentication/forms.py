from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


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
