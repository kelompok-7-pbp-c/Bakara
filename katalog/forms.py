from django import forms
from .models import Barang

class BarangForm(forms.ModelForm):
    class Meta:
        model = Barang
        fields = ['nama', 'deskripsi', 'kategori', 'jenis', 'kondisi', 'harga', 'lokasi', 'foto']
        widgets = {
            'nama': forms.TextInput(attrs={
                'placeholder': 'Contoh: Kalkulator Casio FX-991EX',
                'class': 'form-input',
            }),
            'deskripsi': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Deskripsikan kondisi barang...',
                'class': 'form-input',
            }),
            'kategori': forms.Select(attrs={'class': 'form-input'}),
            'jenis': forms.Select(attrs={'class': 'form-input'}),
            'kondisi': forms.Select(attrs={'class': 'form-input'}),
            'harga': forms.NumberInput(attrs={
                'placeholder': 'Wajib diisi jika dijual, kosongkan jika donasi/pinjam',
                'class': 'form-input',
                'min': 0,
            }),
            'lokasi': forms.TextInput(attrs={
                'placeholder': 'Opsional — lokasi bisa disepakati langsung dengan pembeli',
                'class': 'form-input',
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
        }
        error_messages = {
            'foto': {
                'required': 'Foto barang wajib diunggah.',
                'invalid': 'Unggah berkas gambar yang valid.',
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        jenis = cleaned_data.get('jenis')
        harga = cleaned_data.get('harga')

        if jenis == Barang.DONASI or jenis == Barang.PINJAM:
            # Barang donasi/pinjam tidak perlu harga
            cleaned_data['harga'] = None
        elif jenis == Barang.JUAL:
            if not harga or harga <= 0:
                self.add_error(
                    'harga',
                    'Barang yang dijual wajib mencantumkan harga lebih dari Rp 0.'
                )

        return cleaned_data

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        # Validasi wajib foto
        if not foto and not (self.instance and self.instance.pk and self.instance.foto):
            self.add_error('foto', 'Foto barang wajib diunggah.')

        if foto:
            # Validasi batas ukuran file (Maksimum 5 MB)
            max_size = 5 * 1024 * 1024  # 5 Megabytes
            if foto.size > max_size:
                raise forms.ValidationError("Ukuran berkas foto tidak boleh melebihi 5 MB.")

        return foto