from django.urls import path

from . import api_views

app_name = 'minat_api'

urlpatterns = [
    path('minat/', api_views.minat_list, name='minat-list'),
    path('minat/<uuid:minat_id>/', api_views.minat_detail, name='minat-detail'),
    path('minat/<uuid:minat_id>/proses-transaksi/', api_views.minat_proses_transaksi, name='minat-proses-transaksi'),
]
