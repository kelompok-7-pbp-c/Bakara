from django.urls import path
from transaksi import api_views

app_name = 'transaksi_api'

urlpatterns = [
    path('transaksi/', api_views.transaksi_list, name='transaksi-list'),
    path('transaksi/<uuid:transaksi_id>/', api_views.transaksi_detail, name='transaksi-detail'),
    path('transaksi/<uuid:transaksi_id>/aksi/', api_views.transaksi_aksi, name='transaksi-aksi'),
]
