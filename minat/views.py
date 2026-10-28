from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Exists, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from katalog.models import Barang
from transaksi.models import Transaksi
from .models import MinatBarang


@login_required
@require_POST
def tandai_minat(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)

    if barang.penjual_id == request.user.id:
        messages.error(request, 'Kamu tidak bisa menandai minat pada barang sendiri.')
    elif barang.status != Barang.TERSEDIA:
        messages.error(request, 'Barang ini sudah tidak tersedia.')
    else:
        _, dibuat = MinatBarang.objects.get_or_create(
            barang=barang,
            pembeli=request.user,
        )
        if dibuat:
            messages.success(request, 'Minat kamu berhasil dicatat. Lihat kontak penjual di halaman Minat & Kontak.')
        else:
            messages.info(request, 'Kamu sudah menandai minat pada barang ini.')

    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required
@require_POST
def batalkan_minat(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)
    minat = MinatBarang.objects.filter(barang=barang, pembeli=request.user).first()

    if minat:
        minat.delete()
        messages.success(request, 'Minat kamu berhasil dibatalkan.')
    else:
        messages.info(request, 'Kamu belum menandai minat pada barang ini.')
    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required
def daftar_peminat(request):
    status_transaksi_terakhir = Transaksi.objects.filter(
        barang_id=OuterRef('barang_id'),
        pembeli_id=OuterRef('pembeli_id'),
    ).order_by('-dibuat_pada').values('status')[:1]
    transaksi_selesai = Transaksi.objects.filter(
        barang_id=OuterRef('barang_id'),
        pembeli_id=OuterRef('pembeli_id'),
        status=Transaksi.SELESAI,
    )

    minat_saya = MinatBarang.objects.filter(
        pembeli=request.user,
    ).select_related(
        'barang', 'barang__penjual', 'barang__penjual__profile'
    ).annotate(
        transaksi_status=Subquery(status_transaksi_terakhir),
        transaksi_selesai=Exists(transaksi_selesai),
    ).filter(transaksi_selesai=False)

    peminat_barang_saya = MinatBarang.objects.filter(
        barang__penjual=request.user,
    ).select_related(
        'barang', 'pembeli', 'pembeli__profile'
    ).annotate(
        transaksi_status=Subquery(status_transaksi_terakhir),
        transaksi_selesai=Exists(transaksi_selesai),
    ).filter(transaksi_selesai=False)

    return render(request, 'minat/daftar_peminat.html', {
        'brand_name': 'Bakara',
        'minat_saya': minat_saya,
        'peminat_barang_saya': peminat_barang_saya,
    })


@login_required
@require_POST
def proses_transaksi(request, minat_id):
    """Penjual memilih satu peminat untuk dilanjutkan ke transaksi resmi."""
    with transaction.atomic():
        minat = get_object_or_404(
            MinatBarang.objects.select_related('barang'),
            pk=minat_id,
            barang__penjual=request.user,
        )
        barang = Barang.objects.select_for_update().get(pk=minat.barang_id)
        if barang.status != Barang.TERSEDIA:
            messages.error(request, 'Barang ini sudah diproses atau tidak tersedia.')
        elif Transaksi.objects.filter(
            barang=barang,
            status__in=[Transaksi.MENUNGGU, Transaksi.DISETUJUI],
        ).exists():
            messages.info(request, 'Barang ini sudah memiliki transaksi aktif.')
        else:
            Transaksi.objects.create(
                barang=barang,
                pembeli=minat.pembeli,
                status=Transaksi.DISETUJUI,
            )
            barang.status = Barang.DALAM_PROSES
            barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(request, f'{minat.pembeli.username} dipilih. Transaksi resmi sudah dibuat.')
    return redirect('transaksi:show_transaction')
