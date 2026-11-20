from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from review.models import Review
from review.permissions import IsReviewerOrReadOnly
from review.serializers import ReviewSerializer
from transaksi.models import Transaksi


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsReviewerOrReadOnly])
def review_list(request):
    if request.method in ("GET", "HEAD"):
        reviews = Review.objects.select_related(
            "reviewer", "reviewee", "transaksi__barang"
        ).all()

        rating_param = request.query_params.get("rating", "").strip()
        if rating_param:
            reviews = reviews.filter(rating=rating_param)

        transaksi_param = request.query_params.get("transaksi", "").strip()
        if transaksi_param:
            reviews = reviews.filter(transaksi_id=transaksi_param)

        serializer = ReviewSerializer(
            reviews, many=True, context={"request": request}
        )
        return Response(serializer.data)

    serializer = ReviewSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    transaksi = get_object_or_404(
        Transaksi.objects.select_related("barang__penjual", "pembeli"),
        pk=serializer.validated_data["transaksi"].pk,
    )
    penjual = transaksi.barang.penjual

    if request.user.id == penjual.id:
        raise PermissionDenied(
            "Penjual tidak dapat memberikan ulasan untuk transaksi ini."
        )

    if request.user.id != transaksi.pembeli_id:
        raise PermissionDenied(
            "Hanya pembeli pada transaksi ini yang dapat memberikan ulasan."
        )

    if not transaksi.is_selesai:
        raise ValidationError(
            {"transaksi": ["Ulasan hanya bisa dibuat setelah transaksi selesai."]}
        )

    if Review.objects.filter(transaksi=transaksi, reviewer=request.user).exists():
        raise ValidationError(
            {"transaksi": ["Kamu sudah memberi ulasan untuk transaksi ini."]}
        )

    serializer.save(reviewer=request.user, reviewee=penjual)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsReviewerOrReadOnly])
def review_detail(request, review_id):
    review = get_object_or_404(
        Review.objects.select_related("reviewer", "reviewee", "transaksi__barang"),
        pk=review_id,
    )

    if request.method in ("GET", "HEAD"):
        serializer = ReviewSerializer(review, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        if not review.bisa_dihapus_oleh(request.user):
            raise PermissionDenied(
                "Anda tidak memiliki izin untuk menghapus review ini."
            )
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if not review.bisa_diedit_oleh(request.user):
        raise PermissionDenied("Anda tidak memiliki izin untuk mengubah review ini.")

    serializer = ReviewSerializer(
        review,
        data=request.data,
        partial=(request.method == "PATCH"),
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)