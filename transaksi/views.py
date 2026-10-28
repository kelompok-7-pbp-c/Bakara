from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from katalog.models import Barang
from .models import Transaksi


@login_required(login_url='/auth/login/')
def daftar_transaksi(request):
    transaksi_beli = Transaksi.objects.filter(
        pembeli=request.user
    ).select_related('barang', 'barang__penjual__profile')

    transaksi_jual = Transaksi.objects.filter(
        barang__penjual=request.user
    ).select_related('barang', 'pembeli__profile')

    transaksi_list = (transaksi_beli | transaksi_jual).order_by('-dibuat_pada')

    context = {
        'brand_name': 'Bakara',
        'transaksi_list': transaksi_list,
        'transaksi_beli': transaksi_beli,
        'transaksi_jual': transaksi_jual,
    }
    return render(request, 'transaksi.html', context)


@login_required(login_url='/auth/login/')
@require_POST
def buat_transaksi(request, barang_id):
    barang = get_object_or_404(Barang, pk=barang_id)

    if barang.penjual == request.user:
        messages.error(request, 'Kamu tidak bisa mengajukan transaksi untuk barang milikmu sendiri.')
        return redirect('katalog:detail_barang', pk=barang.pk)

    if barang.status != Barang.TERSEDIA:
        messages.error(request, 'Barang ini sudah tidak tersedia.')
        return redirect('katalog:detail_barang', pk=barang.pk)

    sudah_ada = Transaksi.objects.filter(
        barang=barang,
        pembeli=request.user,
        status__in=[Transaksi.MENUNGGU, Transaksi.DISETUJUI],
    ).exists()

    if sudah_ada:
        messages.info(request, 'Kamu sudah memiliki transaksi aktif untuk barang ini.')
        return redirect('transaksi:daftar_transaksi')

    Transaksi.objects.create(
        barang=barang,
        pembeli=request.user,
        catatan_pembeli=request.POST.get('catatan_pembeli', '').strip(),
    )

    messages.success(request, f'Pengajuan transaksi untuk "{barang.nama}" berhasil diajukan!')
    return redirect('transaksi:daftar_transaksi')


@login_required(login_url='/auth/login/')
@require_POST
def ubah_status_transaksi(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related('barang'),
        pk=transaksi_id,
    )

    if transaksi.barang.penjual != request.user:
        raise PermissionDenied

    aksi = request.POST.get('aksi')

    with transaction.atomic():
        if aksi == 'setujui' and transaksi.bisa_disetujui_oleh(request.user):
            transaksi.status = Transaksi.DISETUJUI
            transaksi.barang.status = Barang.DALAM_PROSES
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(request, 'Transaksi disetujui. Silakan atur serah terima barang.')

        elif aksi == 'selesai' and transaksi.bisa_diselesaikan_oleh(request.user):
            transaksi.status = Transaksi.SELESAI
            transaksi.barang.status = Barang.SELESAI
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(request, 'Transaksi selesai! Terima kasih sudah berbagi.')

        elif aksi == 'tolak' and transaksi.bisa_ditolak_oleh(request.user):
            transaksi.status = Transaksi.DITOLAK
            transaksi.barang.status = Barang.TERSEDIA
            transaksi.save(update_fields=['status', 'diperbarui_pada'])
            transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.info(request, 'Transaksi telah ditolak.')

        else:
            messages.error(request, 'Aksi tidak valid atau status transaksi tidak memungkinkan.')

    return redirect('transaksi:daftar_transaksi')


@login_required(login_url='/auth/login/')
@require_POST
def batalkan_transaksi(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related('barang'),
        pk=transaksi_id,
    )

    if not transaksi.bisa_dibatalkan_oleh(request.user):
        raise PermissionDenied

    with transaction.atomic():
        transaksi.status = Transaksi.DIBATALKAN
        transaksi.barang.status = Barang.TERSEDIA
        transaksi.save(update_fields=['status', 'diperbarui_pada'])
        transaksi.barang.save(update_fields=['status', 'diperbarui_pada'])

    messages.success(request, 'Transaksi berhasil dibatalkan dan barang kembali tersedia.')
    return redirect('transaksi:daftar_transaksi')


@login_required(login_url='/auth/login/')
def transaksi_json(request):
    transaksi_list = Transaksi.objects.filter(
        models.Q(pembeli=request.user) | models.Q(barang__penjual=request.user)
    ).select_related(
        'barang',
        'pembeli',
        'pembeli__profile',
        'barang__penjual',
        'barang__penjual__profile'
    ).order_by('-dibuat_pada')

    data = []
    for t in transaksi_list:
        is_penjual = (t.barang.penjual_id == request.user.id)
        partner = t.pembeli if is_penjual else t.barang.penjual
        partner_profile = getattr(partner, 'profile', None)

        partner_name = partner.username
        partner_wa = ''
        if partner_profile:
            partner_name = partner_profile.full_name or partner.username
            partner_wa = partner_profile.whatsapp_link if partner_profile.whatsapp else ''

        if t.barang.jenis == 'donasi':
            partner_role = 'Penerima Donasi' if is_penjual else 'Donatur'
            jenis_label = 'Donasi'
            harga_display = 'Gratis'
        elif t.barang.jenis == 'pinjam':
            partner_role = 'Peminjam' if is_penjual else 'Pemilik Barang'
            jenis_label = 'Pinjam'
            harga_display = 'Dipinjamkan'
        else:
            partner_role = 'Pembeli' if is_penjual else 'Penjual'
            jenis_label = 'Jual'
            harga_display = t.barang.harga_display

        barang_foto = ''
        if t.barang.foto:
            try:
                barang_foto = t.barang.foto.url
            except ValueError:
                barang_foto = ''

        data.append({
            'id': str(t.id),
            'barang_id': str(t.barang.id),
            'barang_nama': t.barang.nama,
            'barang_jenis': t.barang.jenis,
            'barang_jenis_label': jenis_label,
            'barang_harga': harga_display,
            'barang_lokasi': t.barang.lokasi or '',
            'barang_foto': barang_foto,
            'is_penjual': is_penjual,
            'partner_role': partner_role,
            'partner_name': partner_name,
            'partner_wa': partner_wa,
            'status': t.status,
            'status_label': t.get_status_display(),
            'catatan_pembeli': t.catatan_pembeli,
            'dibuat_pada': t.dibuat_pada.strftime('%d %b %Y, %H:%M'),
        })

    return JsonResponse({'transaksi': data, 'total': len(data)})