from django.urls import path
from transaksi.views import (
    daftar_transaksi,
    buat_transaksi,
    ubah_status_transaksi,
    batalkan_transaksi,
    transaksi_json,
)

app_name = "transaksi"

urlpatterns = [
    path("", daftar_transaksi, name="daftar_transaksi"),
    path("buat/<uuid:barang_id>/", buat_transaksi, name="buat_transaksi"),
    path("ubah-status/<uuid:transaksi_id>/", ubah_status_transaksi, name="ubah_status_transaksi"),
    path("batalkan/<uuid:transaksi_id>/", batalkan_transaksi, name="batalkan_transaksi"),

    path("api/list/", transaksi_json, name="transaksi_json"),
]