from django.urls import path
from main.views import (
    show_beranda,
    show_transaksi, show_profil, show_tentang,
)

app_name = 'main'

urlpatterns = [
    path('', show_beranda, name='show_beranda'),
    path('transaksi/', show_transaksi, name='show_transaksi'),
    path('profil/', show_profil, name='show_profil'),
    path('tentang/', show_tentang, name='show_tentang'),
]
