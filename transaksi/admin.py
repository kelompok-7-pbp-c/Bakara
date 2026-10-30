from django.contrib import admin
from .models import Transaksi

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ('barang', 'pembeli', 'status', 'dibuat_pada', 'diperbarui_pada')
    list_filter = ('status', 'dibuat_pada')
    search_fields = ('barang__nama', 'pembeli__username', 'catatan_pembeli')
    readonly_fields = ('id', 'dibuat_pada', 'diperbarui_pada')