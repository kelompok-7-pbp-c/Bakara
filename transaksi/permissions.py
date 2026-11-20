from rest_framework.permissions import BasePermission


class IsPembeliOrPenjual(BasePermission):
    message = 'Anda tidak memiliki izin untuk mengakses transaksi ini.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.pembeli == user or obj.barang.penjual == user
