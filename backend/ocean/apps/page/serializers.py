from django.http import Http404
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
    previous = serializers.UUIDField(required=False, allow_null=True)

    @staticmethod
    def validate_page(page):
        try:
            return Page.objects.only("id", "uid").get(uid=page)
        except Page.DoesNotExist:
            raise serializers.ValidationError("Page not found.")

    def validate(self, data):
        next_uid = data.get("next")
        previous_uid = data.get("previous")

        page = data["page"]

        if not (next_uid or previous_uid):
            if page.blocks.exists():
                raise serializers.ValidationError("Must link new block with existing blocks.")
            return data

        if next_uid and previous_uid and next_uid == previous_uid:
            raise serializers.ValidationError("Same block can't be both next and previous")

        to_search = set()
        if next_uid:
            to_search.add(next_uid)
        if previous_uid:
            to_search.add(previous_uid)

        linked_blocks = (
            Block.objects.filter(uid__in=to_search, page_id=page.id)
            .only("id", "uid", "next_id", "previous_id")
            .in_bulk(field_name="uid")
        )
        if missing_blocks := to_search.difference(set(linked_blocks)):
            raise serializers.ValidationError(f"Blocks not found: {missing_blocks}")

        # For a new last node in the list, its previous must be the last node at the curent time.
        if not next_uid and linked_blocks[previous_uid].next_id is not None:
            raise serializers.ValidationError("New last block must be linked to the current last block")

        # For a new first node in the list, its next must be the first node at the curent time.
        if not previous_uid and linked_blocks[next_uid].previous_id is not None:
            raise serializers.ValidationError("New first block must be linked to the current first block")

        if next_uid:
            data["next"] = linked_blocks[next_uid]
        if previous_uid:
            data["previous"] = linked_blocks[previous_uid]

        return data

    def create(self, validated_data: dict):
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

    def to_representation(self, instance):
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
