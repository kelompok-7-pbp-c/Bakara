from rest_framework.permissions import BasePermission


class IsAuthenticatedMinatParticipant(BasePermission):
    message = 'Anda harus login untuk mengakses minat.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.pembeli_id == request.user.id or obj.barang.penjual_id == request.user.id
