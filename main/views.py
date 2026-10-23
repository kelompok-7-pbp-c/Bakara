from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from authentication.models import Profile


def show_beranda(request):
    context = {
        'brand_name': 'Bakara'
    }
    return render(request, 'beranda.html', context)

# NOTE:
# show_katalog telah dipindahkan ke katalog/views.py
# URL /katalog/ sekarang ditangani oleh app `katalog`.

@login_required
def show_transaksi(request):
    return render(request, 'transaksi.html')

@login_required
def show_profil(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profil.html', {'profile': profile})

def show_tentang(request):
    return render(request, 'tentang.html')