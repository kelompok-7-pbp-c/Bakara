from django import forms

from .models import Barang


class BarangForm(forms.ModelForm):
    """Form untuk membuat dan mengedit listing barang."""

    class Meta:
        model  = Barang
        fields = [
            'nama', 'deskripsi', 'kategori',
            'jenis', 'kondisi', 'harga',
            'lokasi', 'foto_url',
        ]
        widgets = {
            'nama': forms.TextInput(attrs={
                'placeholder': 'Contoh: Kalkulator Casio FX-991EX',
                'class': 'form-input',
            }),
            'deskripsi': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Deskripsikan kondisi, kelengkapan, dan info penting lainnya…',
                'class': 'form-input',
            }),
            'kategori': forms.Select(attrs={'class': 'form-input'}),
            'jenis':    forms.Select(attrs={'class': 'form-input'}),
            'kondisi':  forms.Select(attrs={'class': 'form-input'}),
            'harga': forms.NumberInput(attrs={
                'placeholder': 'Kosongkan jika gratis',
                'class': 'form-input',
                'min': 0,
            }),
            'lokasi': forms.TextInput(attrs={
                'placeholder': 'Contoh: Asrama UI Wismarini, Fakultas Teknik UI',
                'class': 'form-input',
            }),
            'foto_url': forms.URLInput(attrs={
                'placeholder': 'https://i.imgur.com/contoh.jpg (opsional)',
                'class': 'form-input',
            }),
        }
        labels = {
            'nama':     'Nama Barang',
            'deskripsi':'Deskripsi',
            'kategori': 'Kategori',
            'jenis':    'Jenis Transaksi',
            'kondisi':  'Kondisi Barang',
            'harga':    'Harga (Rp)',
            'lokasi':   'Lokasi Pengambilan',
            'foto_url': 'URL Foto (opsional)',
        }
        help_texts = {
            'harga':    'Biarkan kosong untuk barang gratis / donasi / pinjaman.',
            'foto_url': 'Paste link gambar langsung (JPG/PNG) dari Imgur, Drive publik, dll.',
        }

    def clean_harga(self):
        harga = self.cleaned_data.get('harga')
        jenis = self.cleaned_data.get('jenis')
        # Jika jenis donasi, paksa harga = None
        if jenis == Barang.DONASI:
            return None
        return harga

