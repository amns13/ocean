from rest_framework import permissions, viewsets

from ocean.apps.page.models import Page
from ocean.apps.page.serializers import PageSerializer


class PageViewSet(viewsets.ModelViewSet):
    """
    This ViewSet automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Additionally we also provide an extra `highlight` action.
    """

    queryset = Page.objects.all()
    serializer_class = PageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # TODO: Also include pages on which user has access. Not for now
        return self.queryset.filter(creator_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
