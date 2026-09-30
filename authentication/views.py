from cas import CASClient
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from authentication.forms import LoginForm, RegisterForm


def _safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return None


def register(request):
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Akun berhasil dibuat! Silakan masuk.')
        return redirect('authentication:login')

    return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Selamat datang kembali, {user.username}!')
        return redirect(_safe_next_url(request) or 'main:show_beranda')

    return render(request, 'login.html', {'form': form, 'next': _safe_next_url(request)})


def _sso_client(request):
    # Service URL harus sama persis saat redirect ke CAS dan saat verifikasi ticket
    scheme = 'https' if request.is_secure() or settings.SSO_UI_FORCE_SERVICE_HTTPS else 'http'
    service_url = f'{scheme}://{request.get_host()}{request.path}'
    return CASClient(version=2, service_url=service_url, server_url=settings.SSO_UI_URL)


def _get_or_create_sso_user(sso_username):
    username = sso_username.lower()
    email = f'{username}@ui.ac.id'

    # Akun yang sudah daftar manual dengan email UI yang sama langsung ditautkan
    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user

    # Hindari mengambil alih akun lain yang kebetulan memakai username yang sama
    candidate, suffix = username, 1
    while User.objects.filter(username__iexact=candidate).exists():
        candidate = f'{username}{suffix}'
        suffix += 1

    user = User(username=candidate, email=email)
    user.set_unusable_password()
    user.save()
    return user


def login_sso(request):
    if request.user.is_authenticated:
        return redirect('main:show_beranda')

    client = _sso_client(request)
    ticket = request.GET.get('ticket')

    if not ticket:
        request.session['sso_next'] = _safe_next_url(request)
        return redirect(client.get_login_url())

    sso_username, _attributes, _ = client.verify_ticket(ticket)
    if not sso_username:
        messages.error(request, 'Login SSO UI gagal. Silakan coba lagi.')
        return redirect('authentication:login')

    user = _get_or_create_sso_user(sso_username)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f'Selamat datang, {user.username}!')
    return redirect(request.session.pop('sso_next', None) or 'main:show_beranda')


@require_POST
def logout_user(request):
    logout(request)
    messages.info(request, 'Kamu telah keluar dari akun.')
    return redirect('main:show_beranda')
