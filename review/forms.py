from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    MAX_KOMENTAR = 500

    class Meta:
        model = Review
        fields = ('rating', 'komentar')
        widgets = {
            'rating': forms.RadioSelect(),
            'komentar': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Ceritakan pengalamanmu bertransaksi...',
            }),
        }
        labels = {
            'rating': 'Rating',
            'komentar': 'Ulasan',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hilangkan opsi kosong "---------" agar RadioSelect hanya menampilkan 1-5
        self.fields['rating'].choices = Review.RATING_CHOICES
        self.fields['komentar'].required = False

    def clean_komentar(self):
        komentar = self.cleaned_data.get('komentar', '').strip()
        if len(komentar) > self.MAX_KOMENTAR:
            raise forms.ValidationError(
                f'Ulasan maksimal {self.MAX_KOMENTAR} karakter.'
            )
        return komentar