from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ocean.apps.page.models import Block, Page
from ocean.apps.page.queries import PAGE_BLOCKS_QUERY
from ocean.apps.page.serializers import BlockCreateUpdateSerializer, PageSerializer


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
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uid"
    serializer_class = BlockCreateUpdateSerializer
    http_method_names = ["post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Block.objects.select_related("page", "next", "previous").only(
            "uid", "content", "page_id", "page__uid", "page__first_block_id", "next_id", "next__uid", "previous__id"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        return super().perform_create(serializer)

    @transaction.atomic
    def perform_update(self, serializer):
        return super().perform_update(serializer)

    @transaction.atomic
    def perform_destroy(self, instance):
        next = instance.next
        try:
            prev = instance.previous
        except Block.previous.RelatedObjectDoesNotExist:
            prev = None

        # If there is a previous block linked to deleted block, link it to the deleted block's next
        if prev:
            prev.next = next
            prev.save(update_fields=["next", "updated_at"])

        page = instance.page
        # If deleted block was the first block of the page, then mark its next as the first block.
        if page.first_block_id == instance.id:
            page.first_block_id = next.id if next else None
            page.save(update_fields=["first_block_id", "updated_at"])

        instance.next = None
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["next", "deleted_at", "updated_at"])
