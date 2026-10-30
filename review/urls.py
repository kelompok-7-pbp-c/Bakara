from django.urls import path
from review.views import (
    show_review,
    create_review,
    edit_review,
    delete_review,
    get_review_json,
)

app_name = "review"

urlpatterns = [
    path("", show_review, name="show_review"),
    path("buat/<uuid:transaksi_id>/", create_review, name="create_review"),
    path("ubah/<uuid:review_id>/", edit_review, name="edit_review"),
    path("hapus/<uuid:review_id>/", delete_review, name="delete_review"),
    path("api/list/", get_review_json, name="get_review_json"),
]