from django.utils.html import strip_tags
from rest_framework import serializers

from review.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.SerializerMethodField()
    reviewee_username = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "transaksi",
            "reviewer",
            "reviewer_username",
            "reviewee",
            "reviewee_username",
            "rating",
            "komentar",
            "dibuat_pada",
            "diperbarui_pada",
            "can_edit",
            "can_delete",
        ]
        read_only_fields = [
            "id",
            "reviewer",
            "reviewee",
            "dibuat_pada",
            "diperbarui_pada",
        ]

    def validate_rating(self, value):
        if value not in (1, 2, 3, 4, 5):
            raise serializers.ValidationError("Rating harus berupa angka 1 sampai 5.")
        return value

    def validate_komentar(self, value):
        return strip_tags(value).strip()

    def get_reviewer_username(self, obj):
        return getattr(obj.reviewer, "username", "")

    def get_reviewee_username(self, obj):
        return getattr(obj.reviewee, "username", "")

    def _get_current_user(self):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        return request.user

    def get_can_edit(self, obj):
        user = self._get_current_user()
        if user is None:
            return False
        return obj.bisa_diedit_oleh(user)

    def get_can_delete(self, obj):
        user = self._get_current_user()
        if user is None:
            return False
        return obj.bisa_dihapus_oleh(user)