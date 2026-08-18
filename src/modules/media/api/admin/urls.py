from django.urls import path

from modules.media.api.admin.views import RequestUploadView

urlpatterns = [
    path("uploads", RequestUploadView.as_view(), name="admin-media-request-upload"),
]
