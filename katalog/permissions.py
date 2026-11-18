from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPenjualOrReadOnly(BasePermission):
    message = 'Anda tidak memiliki izin untuk mengubah atau menghapus barang ini.'

    def has_permission(self, request, view):
        # Semua pengunjung boleh membaca data (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True
        # Operasi WRITE (POST, PUT, PATCH, DELETE) mewajibkan akun yang sudah login
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method in ('PUT', 'PATCH'):
            return obj.bisa_diedit_oleh(request.user)
        if request.method == 'DELETE':
            return obj.bisa_dihapus_oleh(request.user)
        return False