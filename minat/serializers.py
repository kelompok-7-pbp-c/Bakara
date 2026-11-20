from rest_framework import serializers

from .models import MinatBarang


class MinatBarangSerializer(serializers.ModelSerializer):
    barang_nama = serializers.CharField(source='barang.nama', read_only=True)
    penjual_id = serializers.UUIDField(source='barang.penjual_id', read_only=True)
    penjual_username = serializers.CharField(source='barang.penjual.username', read_only=True)
    pembeli_username = serializers.CharField(source='pembeli.username', read_only=True)
    peran = serializers.SerializerMethodField()
    nama_kontak = serializers.SerializerMethodField()
    whatsapp = serializers.SerializerMethodField()
    whatsapp_link = serializers.SerializerMethodField()
    line_id = serializers.SerializerMethodField()

    class Meta:
        model = MinatBarang
        fields = [
            'id', 'barang', 'barang_nama', 'penjual_id', 'penjual_username',
            'pembeli', 'pembeli_username', 'dibuat_pada', 'peran',
            'nama_kontak', 'whatsapp', 'whatsapp_link', 'line_id',
        ]
        read_only_fields = fields

    def _kontak(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        user = obj.barang.penjual if obj.pembeli_id == request.user.id else obj.pembeli
        return getattr(user, 'profile', None)

    def get_peran(self, obj):
        request = self.context.get('request')
        if request is None:
            return ''
        return 'pembeli' if obj.pembeli_id == request.user.id else 'penjual'

    def get_nama_kontak(self, obj):
        profile = self._kontak(obj)
        if profile is None:
            request = self.context.get('request')
            user = obj.barang.penjual if request and obj.pembeli_id == request.user.id else obj.pembeli
            return user.username
        return profile.full_name or profile.user.username

    def get_whatsapp(self, obj):
        profile = self._kontak(obj)
        return profile.whatsapp if profile else ''

    def get_whatsapp_link(self, obj):
        profile = self._kontak(obj)
        return profile.whatsapp_link if profile else ''

    def get_line_id(self, obj):
        profile = self._kontak(obj)
        return profile.line_id if profile else ''
