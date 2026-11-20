from django.db import transaction
from django.db.models import Q
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
from .models import Transaksi
from .permissions import IsPembeliOrPenjual
from .serializers import TransaksiSerializer


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPembeliOrPenjual])
def transaksi_list(request):
    if request.method in ('GET', 'HEAD'):
        queryset = (
            Transaksi.objects
            .filter(Q(pembeli=request.user) | Q(barang__penjual=request.user))
            .select_related(
                'barang',
                'barang__penjual',
                'barang__penjual__profile',
                'pembeli',
                'pembeli__profile',
            )
            .order_by('-dibuat_pada')
        )

        status_filter = request.query_params.get('status', '').strip()
        peran = request.query_params.get('peran', '').strip()

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if peran == 'pembeli':
            queryset = queryset.filter(pembeli=request.user)
        elif peran == 'penjual':
            queryset = queryset.filter(barang__penjual=request.user)

        serializer = TransaksiSerializer(
            queryset,
            many=True,
            context={'request': request},
        )
        return Response({'transaksi': serializer.data, 'total': queryset.count()})

    serializer = TransaksiSerializer(
        data=request.data,
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(pembeli=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPembeliOrPenjual])
def transaksi_detail(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related(
            'barang',
            'barang__penjual',
            'barang__penjual__profile',
            'pembeli',
            'pembeli__profile',
        ),
        pk=transaksi_id,
    )

    permission = IsPembeliOrPenjual()
    if not permission.has_object_permission(request, None, transaksi):
        raise PermissionDenied(permission.message)

    if request.method in ('GET', 'HEAD'):
        serializer = TransaksiSerializer(transaksi, context={'request': request})
        return Response(serializer.data)

    if not transaksi.bisa_dibatalkan_oleh(request.user):
        return Response(
            {'detail': 'Transaksi ini tidak dapat dibatalkan.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        status_awal = transaksi.status
        transaksi.status = Transaksi.DIBATALKAN
        transaksi.save(update_fields=['status', 'diperbarui_pada'])

        if status_awal == Transaksi.DISETUJUI and transaksi.barang.status != Barang.SELESAI:
            transaksi.barang.status = Barang.TERSEDIA
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

    serializer = TransaksiSerializer(transaksi, context={'request': request})
    return Response(serializer.data)


@api_view(['POST', 'PATCH'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPembeliOrPenjual])
def transaksi_aksi(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related('barang', 'barang__penjual'),
        pk=transaksi_id,
    )

    permission = IsPembeliOrPenjual()
    if not permission.has_object_permission(request, None, transaksi):
        raise PermissionDenied(permission.message)

    aksi = request.data.get('aksi', '').strip()
    user = request.user

    with transaction.atomic():
        if aksi == 'setujui':
            if transaksi.barang.penjual != user:
                raise PermissionDenied('Hanya penjual yang dapat menyetujui transaksi.')

            if not transaksi.bisa_disetujui_oleh(user):
                return Response(
                    {'detail': 'Transaksi tidak dapat disetujui pada status saat ini.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sudah_ada_disetujui = Transaksi.objects.filter(
                barang=transaksi.barang,
                status=Transaksi.DISETUJUI,
            ).exclude(pk=transaksi.pk).exists()

            if sudah_ada_disetujui or transaksi.barang.status != Barang.TERSEDIA:
                return Response(
                    {'detail': 'Barang ini sudah dalam proses serah terima dengan orang lain.'},
                    status=status.HTTP_409_CONFLICT,
                )

            transaksi.status = Transaksi.DISETUJUI
            transaksi.barang.status = Barang.DALAM_PROSES
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

        elif aksi == 'tolak':
            if transaksi.barang.penjual != user:
                raise PermissionDenied('Hanya penjual yang dapat menolak transaksi.')

            if not transaksi.bisa_ditolak_oleh(user):
                return Response(
                    {'detail': 'Transaksi tidak dapat ditolak pada status saat ini.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaksi.status = Transaksi.DITOLAK
            transaksi.save(update_fields=['status', 'diperbarui_pada'])

            ada_disetujui = Transaksi.objects.filter(
                barang=transaksi.barang,
                status=Transaksi.DISETUJUI,
            ).exclude(pk=transaksi.pk).exists()

            if not ada_disetujui and transaksi.barang.status != Barang.SELESAI:
                transaksi.barang.status = Barang.TERSEDIA
                transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

        elif aksi == 'selesai':
            if transaksi.barang.penjual != user:
                raise PermissionDenied('Hanya penjual yang dapat menyelesaikan transaksi.')

            if not transaksi.bisa_diselesaikan_oleh(user):
                return Response(
                    {'detail': 'Transaksi tidak dapat diselesaikan pada status saat ini.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaksi.status = Transaksi.SELESAI
            transaksi.barang.status = Barang.SELESAI
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

        elif aksi == 'batalkan':
            if not transaksi.bisa_dibatalkan_oleh(user):
                return Response(
                    {'detail': 'Transaksi ini tidak dapat dibatalkan.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            status_awal = transaksi.status
            transaksi.status = Transaksi.DIBATALKAN
            transaksi.save(update_fields=['status', 'diperbarui_pada'])

            if status_awal == Transaksi.DISETUJUI and transaksi.barang.status != Barang.SELESAI:
                transaksi.barang.status = Barang.TERSEDIA
                transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

        else:
            valid_aksi = ['setujui', 'tolak', 'selesai', 'batalkan']
            return Response(
                {
                    'aksi': [
                        f"Aksi tidak valid. Pilih salah satu dari: {', '.join(valid_aksi)}."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    transaksi.refresh_from_db()
    serializer = TransaksiSerializer(transaksi, context={'request': request})
    return Response(serializer.data)
