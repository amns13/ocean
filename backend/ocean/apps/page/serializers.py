from typing import Any

from django.db.models import QuerySet
from rest_framework import serializers

from ocean.apps.page.models import Block, Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")

    class Meta:
        model = Page
        fields = ["id", "uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug"]
        read_only_fields = ["created_at", "updated_at", "id", "uid", "slug"]


class BlockCreateSerializer(serializers.Serializer):
    """
    Why not use ModelSerializer?
    Due to the relations, 2 separate queries will be triggered for next and previous
    """

    page = serializers.UUIDField()
    content = serializers.CharField()
    next = serializers.UUIDField(required=False, allow_null=True)
    previous = serializers.UUIDField(read_only=True)

    def validate_page(self, page) -> Page:
        try:
            return Page.objects.only("id", "uid").get(uid=page)
        except Page.DoesNotExist:
            raise serializers.ValidationError("Page not found.")

    @staticmethod
    def _get_block_by_uid(page_id: int, uid: str, qs: QuerySet[Block] | None) -> Block:
        if qs is None:
            qs = Block.objects.all()
        try:
            return qs.get(page_id=page_id, uid=uid)
        except Block.DoesNotExist:
            raise serializers.ValidationError(f"Block not found: {uid}")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        page: Page = data["page"]

        if (next_uid := data["next"]) is None:
            next_block = None
            prev_block = (
                Block.objects.filter(page_id=page.id, next__isnull=True)
                .only("id", "uid", "next_id", "previous_id")
                .first()
            )
        else:
            qs = Block.objects.select_related("previous").only(
                "id",
                "uid",
                "next_id",
                "previous_id",
                "previous__id",
                "previous__uid",
                "previous__next_id",
                "previous__previous_id",
            )
            next_block = self._get_block_by_uid(qs=qs, page_id=page.id, uid=next_uid)
            prev_block = next_block.previous

        data["next"] = next_block
        data["previous"] = prev_block

        return data

    def create(self, validated_data: dict) -> Block:
        prev_block = validated_data.pop("previous", None)
        next_block = validated_data.pop("next", None)

        block = Block.objects.create(**validated_data)

        to_update = []

        if prev_block:
            prev_block.next = block
            block.previous = prev_block
            to_update.append(prev_block)

        if next_block:
            next_block.previous = block
            block.next = next_block
            to_update.append(next_block)

        if to_update:
            to_update.append(block)
            Block.objects.bulk_update(to_update, ["previous", "next"])

        return block

    def to_representation(self, instance: Block) -> dict[str, Any]:
        """
        We only want to return page's uid. But, django internally returns the title due to __str__ implementation.
        Hence, we override this method to make sure that uid is returned and no extra queries are performed.
        """
        return {
            "uid": instance.uid,
            "page": instance.page.uid,
            "content": instance.content,
            "next": instance.next.uid if instance.next else None,
            "previous": instance.previous.uid if instance.previous else None,
        }
