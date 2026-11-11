from django.urls import path
from main.views import (
    show_beranda,
    show_transaksi, show_profil, show_tentang, show_kebijakan_privasi,
    show_bantuan,
)

app_name = 'main'

urlpatterns = [
    path('', show_beranda, name='show_beranda'),
    path('profil/', show_profil, name='show_profil'),
    path('tentang/', show_tentang, name='show_tentang'),
    path('kebijakan-privasi/', show_kebijakan_privasi, name='show_kebijakan_privasi'),
    path('bantuan/', show_bantuan, name='show_bantuan'),
]