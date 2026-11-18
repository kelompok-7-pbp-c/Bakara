from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from katalog.models import Barang
from katalog.permissions import IsPenjualOrReadOnly
from katalog.serializers import BarangSerializer


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPenjualOrReadOnly])
def barang_list(request):
    if request.method in ('GET', 'HEAD'):
        queryset = Barang.objects.select_related('penjual').all()

        # Filter opsional lewat query params (?kategori=..., ?jenis=..., ?search=..., ?penjual=..., ?status=...)
        kategori = request.query_params.get('kategori', '').strip()
        jenis = request.query_params.get('jenis', '').strip()
        search_query = request.query_params.get('search', '').strip()
        sort = request.query_params.get('sort', '').strip()
        status_barang = request.query_params.get('status', '').strip()
        penjual_id = request.query_params.get('penjual', '').strip()

        if status_barang:
            queryset = queryset.filter(status=status_barang)
        if penjual_id:
            queryset = queryset.filter(penjual__id=penjual_id)

        # Memanfaatkan method filter_katalog yang sudah ada di BarangQuerySet
        queryset = queryset.filter_katalog(
            kategori=kategori or None,
            jenis=jenis or None,
            search_query=search_query or None,
            sort=sort or None,
        )

        serializer = BarangSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    # Method POST: Tambah barang baru (wajib login)
    serializer = BarangSerializer(
        data=request.data,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(penjual=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'PUT', 'PATCH', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPenjualOrReadOnly])
def barang_detail(request, barang_id):
    barang = get_object_or_404(
        Barang.objects.select_related('penjual'),
        pk=barang_id,
    )

    # Pemeriksaan hak akses level objek untuk operasi ubah / hapus
    if request.method not in ('GET', 'HEAD'):
        permission = IsPenjualOrReadOnly()
        if not permission.has_object_permission(request, None, barang):
            raise PermissionDenied(permission.message)

    if request.method in ('GET', 'HEAD'):
        serializer = BarangSerializer(barang, context={'request': request})
        return Response(serializer.data)

    if request.method == 'DELETE':
        barang.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Method PUT (ganti semua) atau PATCH (ubah sebagian field)
    serializer = BarangSerializer(
        barang,
        data=request.data,
        partial=(request.method == 'PATCH'),
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST', 'PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPenjualOrReadOnly])
def barang_status(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)

    permission = IsPenjualOrReadOnly()
    if not permission.has_object_permission(request, None, barang):
        raise PermissionDenied(permission.message)

    new_status = request.data.get('status', '').strip()
    valid_statuses = dict(Barang.STATUS_CHOICES).keys()

    if new_status not in valid_statuses:
        return Response(
            {
                'status': [
                    f"Status tidak valid. Pilih salah satu dari: {', '.join(valid_statuses)}."
                ]
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    barang.status = new_status
    barang.save(update_fields=['status', 'diperbarui_pada'])
    serializer = BarangSerializer(barang, context={'request': request})
    return Response(serializer.data)