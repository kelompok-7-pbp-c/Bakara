from django.utils import timezone
from rest_framework import serializers

from katalog.models import Barang
from review.models import Review
from .models import Transaksi


class TransaksiSerializer(serializers.ModelSerializer):
    pembeli_username = serializers.CharField(source='pembeli.username', read_only=True)
    penjual_username = serializers.CharField(source='barang.penjual.username', read_only=True)
    penjual_id = serializers.UUIDField(source='barang.penjual.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    barang_nama = serializers.CharField(source='barang.nama', read_only=True)
    barang_jenis = serializers.CharField(source='barang.jenis', read_only=True)
    barang_jenis_label = serializers.SerializerMethodField()
    barang_harga_display = serializers.ReadOnlyField(source='barang.harga_display')
    barang_lokasi = serializers.CharField(source='barang.lokasi', read_only=True)
    barang_foto_url = serializers.SerializerMethodField()

    is_penjual = serializers.SerializerMethodField()
    partner_role = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    partner_wa = serializers.SerializerMethodField()
    partner_line = serializers.SerializerMethodField()
    sudah_diulas = serializers.SerializerMethodField()
    bisa_disetujui = serializers.SerializerMethodField()
    bisa_ditolak = serializers.SerializerMethodField()
    bisa_diselesaikan = serializers.SerializerMethodField()
    bisa_dibatalkan = serializers.SerializerMethodField()
    dibuat_pada_display = serializers.SerializerMethodField()

    class Meta:
        model = Transaksi
        fields = [
            'id',
            'barang',
            'barang_nama',
            'barang_jenis',
            'barang_jenis_label',
            'barang_harga_display',
            'barang_lokasi',
            'barang_foto_url',
            'pembeli',
            'pembeli_username',
            'penjual_id',
            'penjual_username',
            'status',
            'status_display',
            'catatan_pembeli',
            'dibuat_pada',
            'dibuat_pada_display',
            'diperbarui_pada',
            'is_penjual',
            'partner_role',
            'partner_name',
            'partner_wa',
            'partner_line',
            'sudah_diulas',
            'bisa_disetujui',
            'bisa_ditolak',
            'bisa_diselesaikan',
            'bisa_dibatalkan',
        ]
        read_only_fields = [
            'id',
            'pembeli',
            'status',
            'dibuat_pada',
            'diperbarui_pada',
        ]

    def validate_barang(self, value):
        request = self.context.get('request')
        if request and value.penjual == request.user:
            raise serializers.ValidationError(
                'Kamu tidak bisa mengajukan transaksi untuk barang milikmu sendiri.'
            )
        if value.status != Barang.TERSEDIA:
            raise serializers.ValidationError('Barang ini sudah tidak tersedia.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        barang = attrs.get('barang')
        if request and barang:
            sudah_ada = Transaksi.objects.filter(
                barang=barang,
                pembeli=request.user,
                status__in=[Transaksi.MENUNGGU, Transaksi.DISETUJUI],
            ).exists()
            if sudah_ada:
                raise serializers.ValidationError(
                    'Kamu sudah memiliki transaksi aktif untuk barang ini.'
                )
        return attrs

    def _get_user(self):
        request = self.context.get('request')
        return request.user if request else None

    def _get_partner(self, obj):
        user = self._get_user()
        if user is None:
            return None
        is_penjual = obj.barang.penjual_id == user.id
        return obj.pembeli if is_penjual else obj.barang.penjual

    def get_barang_jenis_label(self, obj):
        return {
            Barang.DONASI: 'Donasi',
            Barang.PINJAM: 'Pinjam',
            Barang.JUAL: 'Jual',
        }.get(obj.barang.jenis, obj.barang.jenis)

    def get_barang_foto_url(self, obj):
        if not obj.barang.foto:
            return ''
        try:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.barang.foto.url)
            return obj.barang.foto.url
        except ValueError:
            return ''

    def get_is_penjual(self, obj):
        user = self._get_user()
        if user is None or not user.is_authenticated:
            return False
        return obj.barang.penjual_id == user.id

    def get_partner_role(self, obj):
        user = self._get_user()
        if user is None:
            return ''
        is_penjual = obj.barang.penjual_id == user.id
        jenis = obj.barang.jenis
        if jenis == Barang.DONASI:
            return 'Penerima Donasi' if is_penjual else 'Donatur'
        if jenis == Barang.PINJAM:
            return 'Peminjam' if is_penjual else 'Pemilik Barang'
        return 'Pembeli' if is_penjual else 'Penjual'

    def get_partner_name(self, obj):
        partner = self._get_partner(obj)
        if partner is None:
            return ''
        profile = getattr(partner, 'profile', None)
        if profile and profile.full_name:
            return profile.full_name
        return partner.username

    def get_partner_wa(self, obj):
        partner = self._get_partner(obj)
        if partner is None:
            return ''
        profile = getattr(partner, 'profile', None)
        if profile and profile.whatsapp:
            return profile.whatsapp_link
        return ''

    def get_partner_line(self, obj):
        partner = self._get_partner(obj)
        if partner is None:
            return ''
        profile = getattr(partner, 'profile', None)
        return getattr(profile, 'line_id', '') or ''

    def get_sudah_diulas(self, obj):
        return Review.objects.filter(transaksi=obj).exists()

    def get_bisa_disetujui(self, obj):
        user = self._get_user()
        return user is not None and obj.bisa_disetujui_oleh(user)

    def get_bisa_ditolak(self, obj):
        user = self._get_user()
        return user is not None and obj.bisa_ditolak_oleh(user)

    def get_bisa_diselesaikan(self, obj):
        user = self._get_user()
        return user is not None and obj.bisa_diselesaikan_oleh(user)

    def get_bisa_dibatalkan(self, obj):
        user = self._get_user()
        return user is not None and obj.bisa_dibatalkan_oleh(user)

    def get_dibuat_pada_display(self, obj):
        return timezone.localtime(obj.dibuat_pada).strftime('%d %b %Y, %H:%M')
