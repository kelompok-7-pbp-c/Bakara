import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from minat.models import MinatBarang
from .forms import BarangForm
from .models import Barang


# READ — Halaman Katalog (Untuk cari barang)
def show_katalog(request):
    """Tampilkan halaman katalog dengan filter & sorting."""
    qs = Barang.objects.filter(status=Barang.TERSEDIA)
    if request.user.is_authenticated:
        qs = Barang.objects.filter(
            Q(status=Barang.TERSEDIA) | Q(penjual=request.user)
        )
    qs = qs.select_related('penjual')

    # Filter kategori
    kategori = request.GET.get('kategori', '')
    if kategori:
        qs = qs.filter(kategori=kategori)

    # Filter jenis transaksi
    jenis = request.GET.get('jenis', '')
    if jenis:
        qs = qs.filter(jenis=jenis)

    # Search by nama/deskripsi
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nama__icontains=q) | qs.filter(deskripsi__icontains=q)

    # Sorting
    sort = request.GET.get('sort', '-dibuat_pada')
    SORT_MAP = {
        '-dibuat_pada': '-dibuat_pada',
        'dibuat_pada':   'dibuat_pada',
        'harga':         'harga',
        '-harga':        '-harga',
        'nama':          'nama',
    }
    qs = qs.order_by(SORT_MAP.get(sort, '-dibuat_pada'))

    context = {
        'brand_name':       'Bakara',
        'barang_list':      qs,
        'kategori_choices': Barang.KATEGORI_CHOICES,
        'jenis_choices':    Barang.JENIS_CHOICES,
        'filter_kategori':  kategori,
        'filter_jenis':     jenis,
        'search_query':     q,
        'current_sort':     sort,
        'total_barang':     qs.count(),
    }
    return render(request, 'katalog/katalog.html', context)

# READ — Detail Barang


def detail_barang(request, pk):
    barang = get_object_or_404(Barang, pk=pk)

    sudah_berminat = (
        request.user.is_authenticated
        and MinatBarang.objects.filter(
            barang=barang,
            pembeli=request.user,
        ).exists()
    )
    minat_obj = None
    if request.user.is_authenticated and sudah_berminat:
        minat_obj = MinatBarang.objects.filter(barang=barang, pembeli=request.user).first()

    context = {
        'brand_name': 'Bakara',
        'barang': barang,
        'sudah_berminat': sudah_berminat,
        'minat_obj': minat_obj,
    }
    return render(request, 'katalog/detail_barang.html', context)

# CREATE — Tambah Barang


@login_required
def tambah_barang(request):
    if request.method == 'POST':
        form = BarangForm(request.POST)
        if form.is_valid():
            barang = form.save(commit=False)
            barang.penjual = request.user
            barang.save()
            return redirect('katalog:detail_barang', pk=barang.pk)
    else:
        form = BarangForm()

    return render(request, 'katalog/form_barang.html', {
        'brand_name': 'Bakara',
        'form':       form,
        'mode':       'tambah',
        'page_title': 'Upload Barang Baru',
    })

# UPDATE — Edit Barang


@login_required
def edit_barang(request, pk):
    barang = get_object_or_404(Barang, pk=pk, penjual=request.user)

    if request.method == 'POST':
        form = BarangForm(request.POST, instance=barang)
        if form.is_valid():
            form.save()
            return redirect('katalog:detail_barang', pk=barang.pk)
    else:
        form = BarangForm(instance=barang)

    return render(request, 'katalog/form_barang.html', {
        'brand_name': 'Bakara',
        'form':       form,
        'mode':       'edit',
        'page_title': f'Edit: {barang.nama}',
        'barang':     barang,
    })

# DELETE — Hapus Barang


@login_required
@require_POST
def hapus_barang(request, pk):
    barang = get_object_or_404(Barang, pk=pk, penjual=request.user)
    if barang.minat.filter(transaksi__isnull=False).exists():
        messages.error(request, 'Barang yang sudah memiliki riwayat transaksi tidak bisa dihapus.')
        return redirect('katalog:detail_barang', pk=barang.pk)
    barang.delete()
    return redirect('katalog:show_katalog')

# AJAX — JSON endpoint untuk Fetch API


def katalog_json(request):
    """
    Mengembalikan daftar barang dalam format JSON untuk konsumsi Fetch API.
    Mendukung filter: kategori, jenis, q (search), sort.
    """
    qs = Barang.objects.filter(
        status=Barang.TERSEDIA).select_related('penjual')

    kategori = request.GET.get('kategori', '')
    if kategori:
        qs = qs.filter(kategori=kategori)

    jenis = request.GET.get('jenis', '')
    if jenis:
        qs = qs.filter(jenis=jenis)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(nama__icontains=q) | qs.filter(deskripsi__icontains=q)

    sort = request.GET.get('sort', '-dibuat_pada')
    SORT_MAP = {
        '-dibuat_pada': '-dibuat_pada',
        'dibuat_pada':   'dibuat_pada',
        'harga':         'harga',
        '-harga':        '-harga',
        'nama':          'nama',
    }
    qs = qs.order_by(SORT_MAP.get(sort, '-dibuat_pada'))

    data = [
        {
            'id':            str(b.id),
            'nama':          b.nama,
            'kategori':      b.get_kategori_display(),
            'jenis':         b.jenis,
            'jenis_label':   b.get_jenis_display(),
            'kondisi':       b.get_kondisi_display(),
            'status':        b.status,
            'harga':         b.harga,
            'harga_display': b.harga_display,
            'lokasi':        b.lokasi,
            'foto_url':      b.foto_url,
            'penjual':       b.penjual.username,
            'dibuat_pada':   b.dibuat_pada.isoformat(),
            'detail_url':    f'/katalog/{b.id}/',
        }
        for b in qs
    ]
    return JsonResponse({'barang': data, 'total': len(data)})
