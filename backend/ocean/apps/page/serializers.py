from typing import Any

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import serializers

from ocean.apps.page.models import Block, Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")

    class Meta:
        model = Page
        fields = ["id", "uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug"]
        read_only_fields = ["created_at", "updated_at", "id", "uid", "slug"]

class BlockCreateSerializer(serializers.ModelSerializer):
    page = serializers.SlugRelatedField(slug_field="uid", queryset=Page.objects.only("uid", "first_block_id").all())
    next = serializers.SlugRelatedField(slug_field="uid", queryset=Block.objects.select_related("previous").only("uid", "page_id", "previous__id").all(), allow_null=True)

    class Meta:
        model = Block
        fields = ("page", "next", "content")

    def validate(self, data:dict[str, Any]) -> dict[str, Any]:
        page: Page = data["page"]
        next: Block| None = data["next"]
        if next and next.page_id != page.id:
            raise serializers.ValidationError("next block is in different page.")
        return data

    def create(self, validated_data:dict[str, Any]) -> Block:
        next = validated_data.pop("next", None)
        instance = Block.objects.create(**validated_data)

        if next:
            # TODO: Can we use select_related?
            update_timestamp = timezone.now()
            to_update = []

            try:
                previous = next.previous
            except Block.previous.RelatedObjectDoesNotExist:
                pass
            else:
                previous.next = instance
                previous.updated_at = update_timestamp
                to_update.append(previous)

            instance.next = next
            instance.updated_at = update_timestamp
            to_update.append(instance)
            Block.objects.bulk_update(to_update, fields=["next", "updated_at"])

        page = instance.page
        if not page.first_block_id or (next and page.first_block_id == next.id):
            page.first_block_id = instance.id
            page.save(update_fields=["first_block_id", "updated_at"])

        return instance

