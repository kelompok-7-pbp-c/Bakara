from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def show_beranda(request):
    context = {
        'brand_name': 'Bakara'
    }
    return render(request, 'beranda.html', context)

def show_katalog(request):
    return render(request, 'katalog.html')

@login_required
def show_transaksi(request):
    return render(request, 'transaksi.html')

@login_required
def show_profil(request):
    return render(request, 'profil.html')

def show_tentang(request):
    return render(request, 'tentang.html')