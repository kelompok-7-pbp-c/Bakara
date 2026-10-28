from django.urls import path
from transaksi.views import (
    show_transaction,
    create_transaction,
    update_transaction_status,
    cancel_transaction,
    get_transaction_json,
)

app_name = "transaksi"

urlpatterns = [
    path("", show_transaction, name="show_transaction"),
    path("buat/<uuid:barang_id>/", create_transaction, name="create_transaction"),
    path("ubah-status/<uuid:transaksi_id>/", update_transaction_status, name="update_transaction_status"),
    path("batalkan/<uuid:transaksi_id>/", cancel_transaction, name="cancel_transaction"),
    path("api/list/", get_transaction_json, name="get_transaction_json"),
]