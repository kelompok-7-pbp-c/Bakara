from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from katalog.models import Barang
from .models import MinatBarang, Transaksi


@login_required
@require_POST
def tandai_minat(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)

    if barang.penjual_id == request.user.id:
        messages.error(
            request, 'Kamu tidak bisa menandai minat pada barang sendiri.')
    elif barang.status != Barang.TERSEDIA:
        messages.error(request, 'Barang ini sudah tidak tersedia.')
    else:
        _, dibuat = MinatBarang.objects.get_or_create(
            barang=barang,
            pembeli=request.user,
        )

        if dibuat:
            messages.success(request, 'Minat kamu berhasil dicatat.')
        else:
            messages.info(
                request, 'Kamu sudah menandai minat pada barang ini.')

    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required
@require_POST
def batalkan_minat(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)

    minat = MinatBarang.objects.filter(barang=barang, pembeli=request.user).first()
    if minat and minat.transaksi.filter(status=Transaksi.MENUNGGU).exists():
        messages.error(request, 'Minat tidak bisa dibatalkan selama checkout masih berjalan.')
    elif minat:
        minat.delete()
        messages.success(request, 'Minat kamu berhasil dibatalkan.')
    else:
        messages.info(request, 'Kamu belum menandai minat pada barang ini.')
    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required
def daftar_peminat(request):
    daftar_minat = MinatBarang.objects.filter(
        barang__penjual=request.user,
    ).select_related('barang', 'pembeli', 'pembeli__profile').prefetch_related('transaksi')

    return render(request, 'minat/daftar_peminat.html', {
        'brand_name': 'Bakara',
        'daftar_minat': daftar_minat,
    })


@login_required
@require_POST
def checkout(request, minat_id):
    with transaction.atomic():
        minat = get_object_or_404(
            MinatBarang.objects.select_related('barang'), pk=minat_id,
            pembeli=request.user,
        )
        barang = Barang.objects.select_for_update().get(pk=minat.barang_id)
        if barang.status != Barang.TERSEDIA:
            messages.error(request, 'Barang ini sudah tidak tersedia untuk checkout.')
        else:
            transaksi, dibuat = Transaksi.objects.get_or_create(
                minat=minat, status=Transaksi.MENUNGGU,
            )
            if dibuat:
                barang.status = Barang.DALAM_PROSES
                barang.save(update_fields=['status', 'diperbarui_pada'])
                messages.success(request, 'Checkout diajukan. Hubungi penjual untuk mengatur serah terima.')
            else:
                messages.info(request, 'Checkout untuk barang ini sudah berjalan.')
    return redirect('main:show_transaksi')


@login_required
@require_POST
def ubah_status_transaksi(request, transaksi_id):
    aksi = request.POST.get('aksi')
    with transaction.atomic():
        transaksi = get_object_or_404(
            Transaksi.objects.select_related('minat__barang'), pk=transaksi_id,
            minat__barang__penjual=request.user,
        )
        barang = Barang.objects.select_for_update().get(pk=transaksi.minat.barang_id)
        if transaksi.status != Transaksi.MENUNGGU:
            messages.info(request, 'Transaksi ini sudah berakhir.')
        elif aksi == 'selesai':
            transaksi.status = Transaksi.SELESAI
            barang.status = Barang.SELESAI
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(request, 'Transaksi ditandai selesai.')
        elif aksi == 'batalkan':
            transaksi.status = Transaksi.DIBATALKAN
            barang.status = Barang.TERSEDIA
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(request, 'Transaksi dibatalkan dan barang tersedia kembali.')
        else:
            messages.error(request, 'Aksi transaksi tidak dikenal.')
    return redirect('main:show_transaksi')
