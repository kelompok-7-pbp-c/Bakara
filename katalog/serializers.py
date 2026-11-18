from django.utils.html import strip_tags
from PIL import Image
from rest_framework import serializers
from katalog.models import Barang


class BarangSerializer(serializers.ModelSerializer):
    penjual_username = serializers.CharField(source='penjual.username', read_only=True)
    kategori_display = serializers.CharField(source='get_kategori_display', read_only=True)
    jenis_display = serializers.CharField(source='get_jenis_display', read_only=True)
    kondisi_display = serializers.CharField(source='get_kondisi_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    harga_display = serializers.ReadOnlyField()
    foto_url = serializers.SerializerMethodField()
    bisa_diedit = serializers.SerializerMethodField()
    bisa_dihapus = serializers.SerializerMethodField()

    class Meta:
        model = Barang
        fields = [
            'id',
            'penjual',
            'penjual_username',
            'nama',
            'deskripsi',
            'kategori',
            'kategori_display',
            'jenis',
            'jenis_display',
            'kondisi',
            'kondisi_display',
            'status',
            'status_display',
            'harga',
            'harga_display',
            'lokasi',
            'foto',
            'foto_url',
            'dibuat_pada',
            'diperbarui_pada',
            'bisa_diedit',
            'bisa_dihapus',
        ]
        read_only_fields = ['id', 'penjual', 'dibuat_pada', 'diperbarui_pada']

    def validate_nama(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError('Nama barang tidak boleh kosong.')
        return value

    def validate_deskripsi(self, value):
        return strip_tags(value).strip()

    def validate_lokasi(self, value):
        return strip_tags(value).strip()

    def validate_foto(self, value):
        if not value:
            if self.instance and self.instance.pk and self.instance.foto:
                return self.instance.foto
            raise serializers.ValidationError('Foto barang wajib diunggah.')

        # Validasi batas ukuran file (Maksimum 5 MB) seperti di BarangForm
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Ukuran berkas foto tidak boleh melebihi 5 MB.')

        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError('Berkas yang diunggah bukan gambar yang valid.')
        finally:
            if hasattr(value, 'seek'):
                value.seek(0)

        return value

    def validate(self, attrs):
        jenis = attrs.get('jenis', getattr(self.instance, 'jenis', Barang.JUAL))
        harga = attrs.get('harga', getattr(self.instance, 'harga', None))

        if jenis in (Barang.DONASI, Barang.PINJAM):
            attrs['harga'] = None
        elif jenis == Barang.JUAL:
            if not harga or harga <= 0:
                raise serializers.ValidationError({
                    'harga': 'Barang yang dijual wajib mencantumkan harga lebih dari Rp 0.'
                })

        return attrs

    def get_foto_url(self, obj):
        if not obj.foto:
            return ''
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.foto.url)
        return obj.foto.url

    def get_bisa_diedit(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        return obj.bisa_diedit_oleh(request.user)

    def get_bisa_dihapus(self, obj):
        request = self.context.get('request')
        if request is None:
            return False
        return obj.bisa_dihapus_oleh(request.user)