from django.utils.text import slugify
from rest_framework import serializers

from ocean.apps.page.models import Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")
    slug = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug"]
        read_only_fields = ["created_at", "updated_at", "id", "uid", "slug"]

    def get_slug(self, obj) -> str:
        return slugify(obj.title)[:127]
