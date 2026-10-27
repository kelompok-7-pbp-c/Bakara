from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from minat.models import MinatBarang, Transaksi

from .forms import BarangForm
from .models import Barang


def show_katalog(request):
    """Menampilkan halaman katalog barang dengan fitur filter, search, dan sorting."""
    kategori = request.GET.get('kategori', '')
    jenis = request.GET.get('jenis', '')
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '-dibuat_pada')

    barang_list = Barang.objects.tersedia().filter_katalog(
        kategori=kategori,
        jenis=jenis,
        search_query=q,
        sort=sort
    )

    context = {
        'brand_name': 'Bakara',
        'barang_list': barang_list,
        'kategori_choices': Barang.KATEGORI_CHOICES,
        'jenis_choices': Barang.JENIS_CHOICES,
        'filter_kategori': kategori,
        'filter_jenis': jenis,
        'search_query': q,
        'current_sort': sort,
        'total_barang': barang_list.count(),
    }
    return render(request, 'katalog/katalog.html', context)


def detail_barang(request, pk):
    """Menampilkan detail spesifik suatu barang beserta data profil penjual."""
    barang = get_object_or_404(Barang.objects.select_related('penjual__profile'), pk=pk)

    sudah_berminat = False
    minat_obj = None
    ada_transaksi_aktif = False

    if request.user.is_authenticated and request.user != barang.penjual:
        minat_obj = MinatBarang.objects.filter(
            barang=barang, pembeli=request.user
        ).prefetch_related('transaksi').first()
        sudah_berminat = minat_obj is not None
        if minat_obj:
            ada_transaksi_aktif = minat_obj.transaksi.filter(
                status=Transaksi.MENUNGGU
            ).exists()

    context = {
        'brand_name': 'Bakara',
        'barang': barang,
        'sudah_berminat': sudah_berminat,
        'minat_obj': minat_obj,
        'ada_transaksi_aktif': ada_transaksi_aktif,
    }
    return render(request, 'katalog/detail_barang.html', context)


@login_required
def tambah_barang(request):
    """Menangani penambahan listing barang baru oleh user yang sedang login."""
    if request.method == 'POST':
        form = BarangForm(request.POST)
        if form.is_valid():
            barang = form.save(commit=False)
            barang.penjual = request.user
            barang.save()
            messages.success(request, f'Barang "{barang.nama}" berhasil dipublikasikan.')
            return redirect('katalog:detail_barang', pk=barang.pk)
    else:
        form = BarangForm()

    return render(request, 'katalog/form_barang.html', {
        'brand_name': 'Bakara',
        'form': form,
        'mode': 'tambah',
        'page_title': 'Pasang Barang',
    })


@login_required
def edit_barang(request, pk):
    """Menangani pengeditan barang hanya jika user adalah pemilik atau staff/admin."""
    barang = get_object_or_404(Barang, pk=pk)
    if not barang.bisa_diedit_oleh(request.user):
        raise PermissionDenied("Kamu tidak memiliki izin untuk mengedit barang ini.")

    if request.method == 'POST':
        form = BarangForm(request.POST, instance=barang)
        if form.is_valid():
            form.save()
            messages.success(request, f'Perubahan pada "{barang.nama}" berhasil disimpan.')
            return redirect('katalog:detail_barang', pk=barang.pk)
    else:
        form = BarangForm(instance=barang)

    return render(request, 'katalog/form_barang.html', {
        'brand_name': 'Bakara',
        'form': form,
        'mode': 'edit',
        'page_title': f'Edit: {barang.nama}',
        'barang': barang,
    })


@login_required
@require_POST
def hapus_barang(request, pk):
    """Menangani penghapusan barang hanya jika user adalah pemilik atau staff/admin."""
    barang = get_object_or_404(Barang, pk=pk)
    if not barang.bisa_dihapus_oleh(request.user):
        raise PermissionDenied("Kamu tidak memiliki izin untuk menghapus barang ini.")

    nama_barang = barang.nama
    barang.delete()

    if request.user.is_staff and request.user != barang.penjual:
        messages.warning(request, f'Barang "{nama_barang}" telah dihapus oleh Admin.')
    else:
        messages.success(request, f'Listing "{nama_barang}" berhasil dihapus.')

    return redirect('katalog:show_katalog')


def katalog_json(request):
    """Mengembalikan data barang dalam format JSON beserta info profil penjual."""
    kategori = request.GET.get('kategori', '')
    jenis = request.GET.get('jenis', '')
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '-dibuat_pada')

    qs = Barang.objects.tersedia().filter_katalog(
        kategori=kategori,
        jenis=jenis,
        search_query=q,
        sort=sort
    )

    data = []
    for b in qs:
        profile = getattr(b.penjual, 'profile', None)
        data.append({
            'id': str(b.id),
            'nama': b.nama,
            'kategori': b.get_kategori_display(),
            'jenis': b.jenis,
            'jenis_label': b.get_jenis_display(),
            'kondisi': b.get_kondisi_display(),
            'status': b.status,
            'harga': b.harga,
            'harga_display': b.harga_display,
            'lokasi': b.lokasi,
            'foto_url': b.foto_url,
            'penjual': {
                'username': b.penjual.username,
                'nama': getattr(profile, 'full_name', '') or b.penjual.username,
                'fakultas': getattr(profile, 'get_faculty_display', lambda: '')(),
                'angkatan': getattr(profile, 'angkatan', None),
            },
            'dibuat_pada': b.dibuat_pada.isoformat(),
            'detail_url': f'/katalog/{b.id}/',
        })

    return JsonResponse({'barang': data, 'total': len(data)})