from django.urls import include, path
from rest_framework.routers import SimpleRouter

from ocean.apps.page import views

router = SimpleRouter()

router.register(r"pages", views.PageViewSet, "page")
router.register(r"blocks", views.BlockCreateUpdateDestroyViewSet, "block")

urlpatterns = [path("", include(router.urls))]
