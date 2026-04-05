from typing import Any

from django.db.models.aggregates import Max
from django.utils import timezone
from rest_framework import serializers

from ocean.apps.page.models import Block, Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")

    class Meta:
        model = Page
        fields = ("uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug")
        read_only_fields = ("created_at", "updated_at", "uid", "slug")


class BlockCreateUpdateSerializer(serializers.ModelSerializer):
    page = serializers.SlugRelatedField(
        slug_field="uid", queryset=Page.objects.annotate(last_block_index=Max("blocks__index")).only("uid").all()
    )

    class Meta:
        model = Block
        fields = ("uid", "page", "content")
        read_only_fields = ("uid",)

    def validate_page(self, page: Page) -> Page:
        if self.instance:
            raise serializers.ValidationError("Can't be sent in update requests.")
        return page

    def create(self, validated_data: dict[str, Any]) -> Block:
        page = validated_data["page"]
        validated_data["index"] = page.last_block_index + 1 if page.last_block_index else 1
        return super().create(validated_data)
