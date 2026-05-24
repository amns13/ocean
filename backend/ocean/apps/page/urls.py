from django.urls import include, path
from rest_framework.routers import SimpleRouter

from ocean.apps.page import views
from ocean.apps.page.views import PageImageDownloadView

router = SimpleRouter()

router.register(r"pages", views.PageViewSet, "page")
router.register(r"blocks", views.BlockCreateUpdateDestroyViewSet, "block")

urlpatterns = [path("", include(router.urls))]

urlpatterns += [
    path(
        "pages/<uuid:page_uid>/download-image/<uuid:image_uid>/",
        PageImageDownloadView.as_view(),
        name="page-image-download",
    )
]
