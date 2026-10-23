from django.urls import path

from . import views

app_name = 'katalog'

urlpatterns = [
    # Read 
    path('', views.show_katalog, name='show_katalog'),
    path('<uuid:pk>/', views.detail_barang, name='detail_barang'),
    # Create 
    path('tambah/', views.tambah_barang, name='tambah_barang'),
    # Update 
    path('<uuid:pk>/edit/', views.edit_barang, name='edit_barang'),
    # Delete 
    path('<uuid:pk>/hapus/', views.hapus_barang, name='hapus_barang'),
    # AJAX / JSON endpoints 
    path('api/list/', views.katalog_json, name='katalog_json'),
]

