from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ocean.apps.page.models import Block, Page
from ocean.apps.page.serializers import BlockCreateUpdateSerializer, PageSerializer


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

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True)
    def blocks(self, request, *args, **kwargs):
        page = self.get_object()

        blocks_qs = page.blocks.order_by("index").only("uid", "content", "page_id")
        blocks = [{"uid": block.uid, "content": block.content} for block in blocks_qs]
        return Response(blocks)


class BlockCreateUpdateDestroyViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "uid"
    serializer_class = BlockCreateUpdateSerializer
    queryset = Block.objects.all()
    http_method_names = ["post", "patch", "delete", "head", "options"]
