from django.urls import include, path
from rest_framework.routers import SimpleRouter

from ocean.apps.page import views

router = SimpleRouter()

router.register(r"", views.PageViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
