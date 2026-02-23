from rest_framework import serializers

from ocean.apps.page.models import Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")

    class Meta:
        model = Page
        fields = ["id", "uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug"]
        read_only_fields = ["created_at", "updated_at", "id", "uid", "slug"]
