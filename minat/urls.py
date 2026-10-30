from django.urls import path

from . import views

app_name = 'minat'

urlpatterns = [
    path('peminat/', views.daftar_peminat, name='daftar_peminat'),
    path('<uuid:barang_id>/tandai/', views.tandai_minat, name='tandai_minat'),
    path('<uuid:barang_id>/batalkan/',
         views.batalkan_minat, name='batalkan_minat'),
    path('<uuid:minat_id>/proses-transaksi/',
         views.proses_transaksi, name='proses_transaksi'),
]
