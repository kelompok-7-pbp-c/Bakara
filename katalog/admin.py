from django.contrib import admin

from .models import Barang


@admin.register(Barang)
class BarangAdmin(admin.ModelAdmin):
    list_display  = ('nama', 'penjual', 'kategori', 'jenis', 'kondisi', 'status', 'harga_display', 'dibuat_pada')
    list_filter   = ('kategori', 'jenis', 'kondisi', 'status')
    search_fields = ('nama', 'deskripsi', 'penjual__username')
    readonly_fields = ('id', 'dibuat_pada', 'diperbarui_pada')
    ordering      = ('-dibuat_pada',)
