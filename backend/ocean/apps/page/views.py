import hashlib
import logging

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from ocean.apps.page.models import Block, Image, Page, PageImage
from ocean.apps.page.serializers import BlockCreateUpdateSerializer, PageSerializer

logger = logging.getLogger(__name__)


class PageViewSet(viewsets.ModelViewSet):
    """
    This ViewSet automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    # TODO: Apply RBAC.
    """

    queryset = Page.objects.order_by("-id")
    serializer_class = PageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "uid"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "upload_image":
            qs = qs.only("id", "uid")
        return qs

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True)
    def blocks(self, request, *args, **kwargs):
        page = self.get_object()

        blocks_qs = page.blocks.order_by("index").only("uid", "content", "page_id")
        blocks = [{"uid": block.uid, "content": block.content} for block in blocks_qs]
        return Response(blocks)

    @action(detail=True, methods=["POST"], url_path="upload-image")
    def upload_image(self, request, *args, **kwargs):
        page = self.get_object()
        data = request.data
        content_hash = hashlib.file_digest(data["image"], "sha256").hexdigest()

        image, created = Image.objects.get_or_create(
            content_hash=content_hash, defaults={"uploaded_by_id": request.user.id, "image": data["image"]}
        )

        if created:
            logger.info("Uploading new image. | Page id: %s | Content hash: %s", page.uid, content_hash)
            # If image is newly created, then we are sure that existing mappings don't exist.
            PageImage.objects.create(image=image, page=page, user=request.user, name=data["image"].name)
        else:
            logger.info("Image already exists. | Page id: %s | Content hash: %s", page.uid, content_hash)
            PageImage.objects.get_or_create(
                image=image, page=page, defaults={"user": request.user, "name": data["image"].name}
            )

        return Response(
            {
                "image_url": f"{settings.API_DOMAIN_PREFIX}{reverse('page:page-image-download', kwargs={'page_uid': page.uid, 'image_uid': image.uid})}"
            }
        )


class BlockCreateUpdateDestroyViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "uid"
    serializer_class = BlockCreateUpdateSerializer
    queryset = Block.objects.all()
    http_method_names = ["post", "patch", "delete", "head", "options"]


class PageImageDownloadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, page_uid: str, image_uid: str):
        page_image = get_object_or_404(
            PageImage.objects.select_related("image"), page__uid=page_uid, image__uid=image_uid
        )
        return FileResponse(page_image.image.image.file.open("rb"), filename=page_image.name, as_attachment=False)
