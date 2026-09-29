from django.shortcuts import render

def show_beranda(request):
    context = {
        'brand_name': 'Bakara'
    }
    return render(request, 'beranda.html', context)

def show_katalog(request):
    return render(request, 'katalog.html')

def show_transaksi(request):
    return render(request, 'transaksi.html')

def show_profil(request):
    return render(request, 'profil.html')

def show_tentang(request):
    return render(request, 'tentang.html')