from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsReviewerOrReadOnly(BasePermission):
    message = "Anda tidak memiliki izin untuk mengubah atau menghapus review ini."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method == "DELETE":
            return obj.bisa_dihapus_oleh(request.user)
        return obj.bisa_diedit_oleh(request.user)