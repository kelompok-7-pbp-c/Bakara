from django.urls import path
from katalog import api_views

app_name = 'katalog_api'

urlpatterns = [
    path('barang/', api_views.barang_list, name='barang-list'),
    path('barang/<uuid:barang_id>/', api_views.barang_detail, name='barang-detail'),
    path('barang/<uuid:barang_id>/status/', api_views.barang_status, name='barang-status'),
]