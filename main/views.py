from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from authentication.models import Profile
from transaksi.models import Transaksi


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
        Q(pembeli=request.user) | Q(barang__penjual=request.user)
    ).select_related('barang', 'pembeli', 'barang__penjual')
    return render(request, 'transaksi.html', {
        'transaksi_list': transaksi_list,
        'brand_name': 'Bakara',
    })

@login_required
def show_profil(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profil.html', {'profile': profile})

def show_tentang(request):
    context = {
        'brand_name': 'Bakara',
    }
    return render(request, 'tentang.html', context)

def show_kebijakan_privasi(request):
    context = {
        'brand_name': 'Bakara',
    }
    return render(request, 'kebijakan_privasi.html', context)

def show_bantuan(request):
    context = {
        'brand_name': 'Bakara',
    }
    return render(request, 'bantuan.html', context)