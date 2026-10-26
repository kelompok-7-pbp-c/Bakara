from xml.etree.ElementTree import ParseError

import requests
from cas import CASClient
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from authentication.forms import LoginForm, ProfileForm, RegisterForm
from authentication.models import Profile


# ---------------------------------------------------------------------------
# Helpers (fungsi privat, prefix _)
# ---------------------------------------------------------------------------

def _safe_next_url(request):
    """
    Memvalidasi URL redirect parameter 'next' agar aman dari open redirect.
    Mengembalikan URL jika valid, None jika tidak.
    """
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


def _build_sso_client(request):
    """
    Membangun instance CASClient untuk autentikasi SSO UI.
    Service URL dikirimkan ke CAS harus identik saat redirect dan verifikasi.
    """
    scheme = 'https' if request.is_secure() or settings.SSO_UI_FORCE_SERVICE_HTTPS else 'http'
    service_url = f'{scheme}://{request.get_host()}{request.path}'
    session = requests.Session()
    # SSO UI menolak User-Agent bawaan python-requests; wajib dioverride.
    session.headers['User-Agent'] = 'Bakara/1.0'
    return CASClient(
        version=2,
        service_url=service_url,
        server_url=settings.SSO_UI_URL,
        session=session,
    )


def _get_or_create_sso_user(sso_username):
    """
    Mengembalikan User yang sudah ada atau membuat User baru dari data SSO UI.
    Akun dengan email @ui.ac.id yang sama akan ditautkan secara otomatis.
    """
    User = get_user_model()
    username = sso_username.lower()
    email = f'{username}@ui.ac.id'

    # Cari user yang sudah terdaftar dengan email yang sama (case-insensitive).
    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user

    # Cegah konflik username dengan menambahkan suffix angka bila perlu.
    candidate, suffix = username, 1
    while User.objects.filter(username__iexact=candidate).exists():
        candidate = f'{username}{suffix}'
        suffix += 1

    user = User(username=candidate, email=email)
    user.set_unusable_password()
    user.save()
    return user


def _prefill_profile_from_sso(user, attributes):
    """
    Mengisi field profil dari atribut CAS/LDAP SSO UI hanya jika masih kosong.
    Tidak menimpa data yang sudah diisi oleh pengguna sebelumnya.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    changed = False

    if not profile.full_name and attributes.get('nama'):
        profile.full_name = attributes['nama'][:100]
        changed = True

    # Dua digit pertama NPM (misal 2306...) merepresentasikan tahun angkatan.
    npm = attributes.get('npm') or ''
    if not profile.angkatan and len(npm) >= 2 and npm[:2].isdigit():
        profile.angkatan = 2000 + int(npm[:2])
        changed = True

    if changed:
        profile.save()


# ---------------------------------------------------------------------------
# Views (fungsi publik)
# ---------------------------------------------------------------------------

def register(request):
    """
    Registrasi akun baru dengan email @ui.ac.id.
    Pengguna yang sudah login diarahkan ke beranda.
    """
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Akun berhasil dibuat! Silakan masuk.')
            return redirect('authentication:login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_user(request):
    """
    Login manual menggunakan username atau email @ui.ac.id.
    Mendukung parameter 'next' yang aman untuk redirect setelah login.
    """
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Selamat datang kembali, {user.username}!')
            return redirect(_safe_next_url(request) or 'main:show_beranda')
    else:
        form = LoginForm(request)

    context = {
        'form': form,
        'next': _safe_next_url(request),
    }
    return render(request, 'login.html', context)


def login_sso(request):
    """
    Alur autentikasi SSO UI menggunakan protokol CAS 2.0.
    Langkah 1 – redirect ke halaman login SSO UI.
    Langkah 2 – CAS redirect kembali ke sini dengan query param 'ticket'.
    """
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    client = _build_sso_client(request)
    ticket = request.GET.get('ticket')

    if not ticket:
        # Simpan URL tujuan sebelum redirect ke SSO agar bisa dikembalikan setelah login.
        request.session['sso_next'] = _safe_next_url(request)
        return redirect(client.get_login_url())

    try:
        sso_username, attributes, _ = client.verify_ticket(ticket)
    except (requests.RequestException, ParseError):
        sso_username = None

    if not sso_username:
        messages.error(request, 'Login SSO UI gagal. Silakan coba lagi.')
        return redirect('authentication:login')

    user = _get_or_create_sso_user(sso_username)
    _prefill_profile_from_sso(user, attributes or {})
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f'Selamat datang, {user.username}!')
    return redirect(request.session.pop('sso_next', None) or 'main:show_beranda')


@require_POST
def logout_user(request):
    """
    Logout pengguna aktif. Hanya menerima metode POST untuk keamanan CSRF.
    """
    logout(request)
    messages.info(request, 'Kamu telah keluar dari akun.')
    return redirect('main:show_beranda')


@login_required
def edit_profile(request):
    """
    Menampilkan dan memproses form pengisian/pembaruan profil mahasiswa.
    Profile dijamin ada karena dibuat otomatis via signal saat User dibuat.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil berhasil diperbarui.')
            return redirect('main:show_profil')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profil_edit.html', {'form': form})
