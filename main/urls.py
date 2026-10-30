from django.urls import path
from main.views import (
<<<<<<< Updated upstream
    show_beranda, show_katalog,
    show_transaksi, show_profil, show_tentang,
=======
    show_beranda,
    show_transaksi, show_profil, show_tentang,show_kebijakan_privasi,
>>>>>>> Stashed changes
)

app_name = 'main'

urlpatterns = [
    path('', show_beranda, name='show_beranda'),
    path('katalog/', show_katalog, name='show_katalog'),
    path('transaksi/', show_transaksi, name='show_transaksi'),
    path('profil/', show_profil, name='show_profil'),
    path('tentang/', show_tentang, name='show_tentang'),
<<<<<<< Updated upstream
]
=======
    path('kebijakan-privasi/', show_kebijakan_privasi, name='show_kebijakan_privasi'),
]
>>>>>>> Stashed changes
