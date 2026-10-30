from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from transaksi.models import Transaksi
from .forms import ReviewForm
from .models import Review


def _nama_pengguna(user):
    profile = getattr(user, 'profile', None)
    if profile and profile.full_name:
        return profile.full_name
    return user.username


def _foto_barang(barang):
    if barang.foto:
        try:
            return barang.foto.url
        except ValueError:
            return ''
    return ''


def _kirim_error_form(request, form):
    for errors in form.errors.values():
        for error in errors:
            messages.error(request, error)


@login_required(login_url='/auth/login/')
def show_review(request):
    context = {
        'brand_name': 'Bakara',
    }
    return render(request, 'review.html', context)


@login_required(login_url='/auth/login/')
@require_POST
def create_review(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related('barang', 'pembeli'),
        pk=transaksi_id,
    )
    penjual = transaksi.barang.penjual

    if request.user.id == penjual.id:
        messages.error(request, 'Penjual tidak dapat memberikan ulasan untuk transaksi ini.')
        return redirect('review:show_review')
    
    if request.user.id != transaksi.pembeli_id:
        raise PermissionDenied

    if not transaksi.is_selesai:
        messages.error(request, 'Ulasan hanya bisa dibuat setelah transaksi selesai.')
        return redirect('review:show_review')

    if Review.objects.filter(transaksi=transaksi, reviewer=request.user).exists():
        messages.info(request, 'Kamu sudah memberi ulasan untuk transaksi ini.')
        return redirect('review:show_review')

    form = ReviewForm(request.POST)
    if not form.is_valid():
        _kirim_error_form(request, form)
        return redirect('review:show_review')

    review = form.save(commit=False)
    review.transaksi = transaksi
    review.reviewer = request.user
    review.reviewee = penjual if request.user.id == transaksi.pembeli_id else transaksi.pembeli
    review.save()

    messages.success(request, 'Ulasan berhasil dikirim. Terima kasih!')
    return redirect('review:show_review')


@login_required(login_url='/auth/login/')
@require_POST
def edit_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    if not review.bisa_diedit_oleh(request.user):
        raise PermissionDenied

    form = ReviewForm(request.POST, instance=review)
    if not form.is_valid():
        _kirim_error_form(request, form)
        return redirect('review:show_review')

    form.save()
    messages.success(request, 'Ulasan berhasil diperbarui.')
    return redirect('review:show_review')


@login_required(login_url='/auth/login/')
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)

    if not review.bisa_dihapus_oleh(request.user):
        raise PermissionDenied

    review.delete()
    messages.success(request, 'Ulasan berhasil dihapus.')
    return redirect('review:show_review')


@login_required(login_url='/auth/login/')
def get_review_json(request):
    diterima = Review.objects.filter(
        reviewee=request.user
    ).select_related('reviewer__profile', 'transaksi__barang')

    diberikan = Review.objects.filter(
        reviewer=request.user
    ).select_related('reviewee__profile', 'transaksi__barang')

    # Transaksi selesai yang menunggu ulasan:
    # HANYA untuk Pembeli (jika user adalah penjual, query menunggu dikosongkan/di-exclude)
    if Transaksi.objects.filter(barang__penjual=request.user).exists() and not Transaksi.objects.filter(pembeli=request.user).exists():
        # Jika user murni penjual pada transaksi tersebut, tidak ada daftar "menunggu" ulasan dari dia
        menunggu = Transaksi.objects.none()
    else:
        # Jika sebagai pembeli, tampilkan transaksi selesai miliknya yang belum diulas
        menunggu = Transaksi.objects.filter(
            pembeli=request.user,
            status=Transaksi.SELESAI,
        ).exclude(
            review__reviewer=request.user
        ).select_related('barang', 'pembeli__profile', 'barang__penjual__profile')

    ringkasan = diterima.aggregate(rata_rata=Avg('rating'), total=Count('id'))
    jumlah_per_rating = {
        row['rating']: row['jumlah']
        for row in diterima.order_by().values('rating').annotate(jumlah=Count('id'))
    }
    sebaran = {str(n): jumlah_per_rating.get(n, 0) for n in range(1, 6)}

    def format_waktu(waktu):
        return timezone.localtime(waktu).strftime('%d %b %Y, %H:%M')

    data_diterima = [{
        'id': str(r.id),
        'transaksi_id': str(r.transaksi_id),
        'barang_nama': r.transaksi.barang.nama,
        'pihak_nama': _nama_pengguna(r.reviewer),
        'rating': r.rating,
        'komentar': r.komentar,
        'dibuat_pada': format_waktu(r.dibuat_pada),
    } for r in diterima]

    data_diberikan = [{
        'id': str(r.id),
        'transaksi_id': str(r.transaksi_id),
        'barang_nama': r.transaksi.barang.nama,
        'pihak_nama': _nama_pengguna(r.reviewee),
        'rating': r.rating,
        'komentar': r.komentar,
        'dibuat_pada': format_waktu(r.dibuat_pada),
    } for r in diberikan]

    data_menunggu = []
    for t in menunggu:
        is_penjual = (t.barang.penjual_id == request.user.id)
        partner = t.pembeli if is_penjual else t.barang.penjual
        data_menunggu.append({
            'transaksi_id': str(t.id),
            'barang_nama': t.barang.nama,
            'barang_foto': _foto_barang(t.barang),
            'pihak_nama': _nama_pengguna(partner),
        })

    return JsonResponse({
        'ringkasan': {
            'rata_rata': round(ringkasan['rata_rata'], 1) if ringkasan['rata_rata'] else 0,
            'total': ringkasan['total'],
            'sebaran': sebaran,
        },
        'diterima': data_diterima,
        'diberikan': data_diberikan,
        'menunggu': data_menunggu,
    })