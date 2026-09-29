from django.contrib import messages
from django.contrib.auth import login, logout
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


@require_POST
def logout_user(request):
    logout(request)
    messages.info(request, 'Kamu telah keluar dari akun.')
    return redirect('main:show_beranda')
