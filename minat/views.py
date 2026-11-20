from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Exists, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from katalog.models import Barang
from transaksi.models import Transaksi
from .models import MinatBarang


@login_required(login_url='/auth/login/')
@require_POST
def tandai_minat(request, barang_id):
    """Catat minat pengguna pada barang yang masih tersedia."""
    # Jika ID tidak cocok dengan barang yang ada, hentikan dengan respons 404.
    barang = get_object_or_404(Barang, pk=barang_id)

    # Penjual tidak dapat menjadi peminat barang miliknya sendiri.
    if barang.penjual_id == request.user.id:
        messages.error(
            request, 'Kamu tidak bisa menandai minat pada barang sendiri.')
    # Minat baru hanya boleh dicatat saat barang masih tersedia.
    elif barang.status != Barang.TERSEDIA:
        messages.error(request, 'Barang ini sudah tidak tersedia.')
    elif MinatBarang.objects.filter(pembeli=request.user).count() >= 3:
        messages.error(
            request, 'Kamu tidak boleh meminati lebih dari 3 barang')
    elif MinatBarang.objects.filter(barang=barang, pembeli=request.user).exists():
        messages.info(request, 'Kamu sudah menandai minat pada barang ini.')
    else:
        # get_or_create mencegah catatan ganda untuk pembeli dan barang yang sama.
        _, dibuat = MinatBarang.objects.get_or_create(
            barang=barang,
            pembeli=request.user,
        )
        # Nilai dibuat menunjukkan apakah catatan baru saja berhasil dibuat.
        if dibuat:
            messages.success(
                request, 'Minat kamu berhasil dicatat. Lihat kontak penjual di halaman Minat & Kontak.')
        else:
            messages.info(
                request, 'Kamu sudah menandai minat pada barang ini.')

    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required(login_url='/auth/login/')
@require_POST
def batalkan_minat(request, barang_id):
    """Hapus minat milik pengguna yang sedang login pada barang tertentu."""
    barang = get_object_or_404(Barang, pk=barang_id)
    # Filter berdasarkan pengguna memastikan minat orang lain tidak terhapus.
    minat = MinatBarang.objects.filter(
        barang=barang, pembeli=request.user).first()

    if minat:
        minat.delete()
        messages.success(request, 'Minat kamu berhasil dibatalkan.')
    else:
        messages.info(request, 'Kamu belum menandai minat pada barang ini.')
    return redirect('katalog:detail_barang', pk=barang.pk)


@login_required(login_url='/auth/login/')
def daftar_peminat(request):
    """Tampilkan minat pengguna sebagai pembeli dan sebagai penjual."""
    # Ambil status transaksi paling baru untuk setiap pasangan barang-pembeli.
    status_transaksi_terakhir = Transaksi.objects.filter(
        barang_id=OuterRef('barang_id'),
        pembeli_id=OuterRef('pembeli_id'),
    ).order_by('-dibuat_pada').values('status')[:1]
    # Pemeriksaan ini dipakai untuk menyembunyikan minat yang transaksinya selesai.
    transaksi_selesai = Transaksi.objects.filter(
        barang_id=OuterRef('barang_id'),
        pembeli_id=OuterRef('pembeli_id'),
        status=Transaksi.SELESAI,
    )

    # Daftar barang yang diminati oleh pengguna saat ini sebagai pembeli.
    minat_saya = MinatBarang.objects.filter(
        pembeli=request.user,
        barang__status__in=[Barang.TERSEDIA, Barang.DALAM_PROSES],
    ).select_related(
        'barang', 'barang__penjual', 'barang__penjual__profile'
    ).annotate(
        transaksi_status=Subquery(status_transaksi_terakhir),
        transaksi_selesai=Exists(transaksi_selesai),
    ).filter(transaksi_selesai=False)

    # Daftar pengguna yang tertarik pada barang milik pengguna saat ini.
    peminat_barang_saya = MinatBarang.objects.filter(
        barang__penjual=request.user,
        barang__status__in=[Barang.TERSEDIA, Barang.DALAM_PROSES],
    ).select_related(
        'barang', 'pembeli', 'pembeli__profile'
    ).annotate(
        transaksi_status=Subquery(status_transaksi_terakhir),
        transaksi_selesai=Exists(transaksi_selesai),
    ).filter(transaksi_selesai=False)

    # select_related pada kedua query mengambil data relasi lebih efisien.
    # Kedua daftar dikirim agar template dapat menampilkan sisi pembeli/penjual.
    return render(request, 'minat/daftar_peminat.html', {
        'brand_name': 'Bakara',
        'minat_saya': minat_saya,
        'peminat_barang_saya': peminat_barang_saya,
    })


@login_required(login_url='/auth/login/')
@require_POST
def proses_transaksi(request, minat_id):
    """Penjual memilih satu peminat untuk dilanjutkan ke transaksi resmi."""
    # atomic menjaga pembuatan transaksi dan perubahan status barang tetap utuh:
    # jika proses gagal, perubahan database dalam blok ini dibatalkan bersama.
    with transaction.atomic():
        # Pastikan minat memang terkait barang milik penjual yang login.
        minat = get_object_or_404(
            MinatBarang.objects.select_related('barang'),
            pk=minat_id,
            barang__penjual=request.user,
        )
        # Kunci baris barang agar permintaan bersamaan tidak memproses barang
        # yang sama pada waktu yang sama.
        barang = Barang.objects.select_for_update().get(pk=minat.barang_id)
        # Jangan lanjutkan jika barang sudah tidak tersedia.
        if barang.status != Barang.TERSEDIA:
            messages.error(
                request, 'Barang ini sudah diproses atau tidak tersedia.')
        # Cegah transaksi baru jika barang sudah memiliki transaksi aktif.
        elif Transaksi.objects.filter(
            barang=barang,
            status__in=[Transaksi.MENUNGGU, Transaksi.DISETUJUI],
        ).exists():
            messages.info(
                request, 'Barang ini sudah memiliki transaksi aktif.')
        else:
            # Penjual memilih peminat ini: buat transaksi dengan status disetujui.
            Transaksi.objects.create(
                barang=barang,
                pembeli=minat.pembeli,
                status=Transaksi.DISETUJUI,
            )
            # Tandai barang sedang diproses agar tidak dipilih untuk transaksi lain.
            barang.status = Barang.DALAM_PROSES
            barang.save(update_fields=['status', 'diperbarui_pada'])
            messages.success(
                request, f'{minat.pembeli.username} dipilih. Transaksi resmi sudah dibuat.')
    # Arahkan pengguna ke halaman daftar/transaksi setelah seluruh pemeriksaan.
    return redirect('transaksi:show_transaction')
