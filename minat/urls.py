from django.urls import path

from . import views

app_name = 'minat'

urlpatterns = [
    path('peminat/', views.daftar_peminat, name='daftar_peminat'),
    path('<uuid:barang_id>/tandai/', views.tandai_minat, name='tandai_minat'),
    path('<uuid:barang_id>/batalkan/',
         views.batalkan_minat, name='batalkan_minat'),
    path('checkout/<int:minat_id>/', views.checkout, name='checkout'),
    path('transaksi/<int:transaksi_id>/status/', views.ubah_status_transaksi, name='ubah_status_transaksi'),
]
