from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from authentication.models import Profile

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
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profil.html', {'profile': profile})

def show_tentang(request):
    return render(request, 'tentang.html')