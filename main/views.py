from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from authentication.models import Profile
from minat.models import Transaksi


def show_beranda(request):
    context = {
        'brand_name': 'Bakara',
    }
    return render(request, 'beranda.html', context)

# NOTE:
# show_katalog telah dipindahkan ke katalog/views.py
# URL /katalog/ sekarang ditangani oleh app `katalog`.

@login_required
def show_transaksi(request):
    transaksi_list = Transaksi.objects.filter(
        Q(minat__pembeli=request.user) | Q(minat__barang__penjual=request.user)
    ).select_related('minat__barang', 'minat__pembeli', 'minat__barang__penjual')
    return render(request, 'transaksi.html', {
        'transaksi_list': transaksi_list,
        'brand_name': 'Bakara',
    })

@login_required
def show_profil(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profil.html', {'profile': profile})

def show_tentang(request):
    return render(request, 'tentang.html')
