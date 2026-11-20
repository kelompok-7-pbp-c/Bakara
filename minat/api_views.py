from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from katalog.models import Barang
from transaksi.models import Transaksi
from .models import MinatBarang
from .permissions import IsAuthenticatedMinatParticipant
from .serializers import MinatBarangSerializer


def _daftar_aktif():
    selesai = Transaksi.objects.filter(
        barang_id=OuterRef('barang_id'), pembeli_id=OuterRef('pembeli_id'),
        status=Transaksi.SELESAI,
    )
    return MinatBarang.objects.filter(
        barang__status__in=[Barang.TERSEDIA, Barang.DALAM_PROSES],
    ).annotate(transaksi_selesai=Exists(selesai)).filter(transaksi_selesai=False)


@api_view(['GET', 'HEAD', 'POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticatedMinatParticipant])
def minat_list(request):
    if request.method in ('GET', 'HEAD'):
        queryset = _daftar_aktif().filter(
            Q(barang__penjual=request.user) | Q(pembeli=request.user)
        ).select_related('barang', 'barang__penjual__profile', 'pembeli__profile')
        peran = request.query_params.get('peran', '').strip()
        if peran == 'pembeli':
            queryset = queryset.filter(pembeli=request.user)
        elif peran == 'penjual':
            queryset = queryset.filter(barang__penjual=request.user)
        elif peran:
            raise ValidationError({'peran': ['Pilih pembeli atau penjual.']})
        serializer = MinatBarangSerializer(queryset.order_by('-dibuat_pada'), many=True, context={'request': request})
        return Response({'minat': serializer.data, 'total': queryset.count()})

    barang_id = request.data.get('barang')
    barang = get_object_or_404(Barang, pk=barang_id)
    if barang.penjual_id == request.user.id:
        raise PermissionDenied('Kamu tidak bisa menandai minat pada barang sendiri.')
    if barang.status != Barang.TERSEDIA:
        raise ValidationError({'barang': ['Barang ini sudah tidak tersedia.']})
    existing = MinatBarang.objects.filter(barang=barang, pembeli=request.user).first()
    if existing:
        serializer = MinatBarangSerializer(existing, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    if MinatBarang.objects.filter(pembeli=request.user).count() >= 3:
        raise ValidationError({'barang': ['Kamu tidak boleh meminati lebih dari 3 barang.']})
    minat = MinatBarang.objects.create(barang=barang, pembeli=request.user)
    return Response(MinatBarangSerializer(minat, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'HEAD', 'DELETE'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticatedMinatParticipant])
def minat_detail(request, minat_id):
    minat = get_object_or_404(MinatBarang.objects.select_related('barang__penjual__profile', 'pembeli__profile'), pk=minat_id)
    permission = IsAuthenticatedMinatParticipant()
    if not permission.has_object_permission(request, None, minat):
        raise PermissionDenied(permission.message)
    if request.method in ('GET', 'HEAD'):
        return Response(MinatBarangSerializer(minat, context={'request': request}).data)
    if minat.pembeli_id != request.user.id:
        raise PermissionDenied('Hanya pembeli yang dapat membatalkan minat ini.')
    minat.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticatedMinatParticipant])
def minat_proses_transaksi(request, minat_id):
    with transaction.atomic():
        minat = get_object_or_404(MinatBarang.objects.select_related('barang', 'pembeli'), pk=minat_id)
        if minat.barang.penjual_id != request.user.id:
            raise PermissionDenied('Hanya penjual barang yang dapat memproses minat ini.')
        barang = Barang.objects.select_for_update().get(pk=minat.barang_id)
        if barang.status != Barang.TERSEDIA:
            return Response({'detail': 'Barang ini sudah diproses atau tidak tersedia.'}, status=status.HTTP_409_CONFLICT)
        if Transaksi.objects.filter(barang=barang, status__in=[Transaksi.MENUNGGU, Transaksi.DISETUJUI]).exists():
            return Response({'detail': 'Barang ini sudah memiliki transaksi aktif.'}, status=status.HTTP_409_CONFLICT)
        transaksi = Transaksi.objects.create(barang=barang, pembeli=minat.pembeli, status=Transaksi.DISETUJUI)
        barang.status = Barang.DALAM_PROSES
        barang.save(update_fields=['status', 'diperbarui_pada'])
    return Response({'transaksi': str(transaksi.pk), 'status': transaksi.status}, status=status.HTTP_201_CREATED)
