from django import forms
from .models import Barang

class BarangForm(forms.ModelForm):
    class Meta:
        model = Barang
        fields = ['nama', 'deskripsi', 'kategori', 'jenis', 'kondisi', 'harga', 'lokasi', 'foto_url']
        widgets = {
            'nama': forms.TextInput(attrs={'placeholder': 'Contoh: Kalkulator Casio FX-991EX', 'class': 'form-input'}),
            'deskripsi': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Deskripsikan kondisi barang...', 'class': 'form-input'}),
            'kategori': forms.Select(attrs={'class': 'form-input'}),
            'jenis': forms.Select(attrs={'class': 'form-input'}),
            'kondisi': forms.Select(attrs={'class': 'form-input'}),
            'harga': forms.NumberInput(attrs={'placeholder': 'Wajib diisi jika dijual, kosongkan jika donasi', 'class': 'form-input', 'min': 0}),
            'lokasi': forms.TextInput(attrs={'placeholder': 'Contoh: Asrama UI, Gedung B FASILKOM', 'class': 'form-input'}),
            'foto_url': forms.URLInput(attrs={'placeholder': 'https://...', 'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        jenis = cleaned_data.get('jenis')
        harga = cleaned_data.get('harga')
        if jenis == Barang.DONASI:
            cleaned_data['harga'] = None
        elif jenis == Barang.JUAL:
            if not harga or harga <= 0:
                self.add_error('harga', 'Untuk barang yang dijual, harga harus lebih dari Rp 0.')
        return cleaned_data