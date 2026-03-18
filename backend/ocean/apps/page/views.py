from django.db import transaction
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ocean.apps.page.models import Block, Page
from ocean.apps.page.queries import PAGE_BLOCKS_QUERY
from ocean.apps.page.serializers import BlockCreateSerializer, PageSerializer


class PageViewSet(viewsets.ModelViewSet):
    """
    This ViewSet automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uid"

    def get_queryset(self):
        # TODO: Also include pages on which user has access. Not for now
        return self.queryset.filter(creator_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True)
    def blocks(self, request, *args, **kwargs):
        page = self.get_object()

        blocks_qs = Block.objects.raw(PAGE_BLOCKS_QUERY, [page.id])
        blocks = [{"uid": block.uid, "content": block.content} for block in blocks_qs]
        return Response(blocks)


class BlockCreateUpdateDestroyViewSet(
    mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    """
    TODO: update the existing blocks next/previous
    """

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uid"

    def get_serializer_class(self):
        if self.action == "create":
            return BlockCreateSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        return super().perform_create(serializer)
