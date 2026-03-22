from typing import Any

from django.utils import timezone
from rest_framework import serializers

from ocean.apps.page.models import Block, Page


class PageSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source="creator_id")

    class Meta:
        model = Page
        fields = ["id", "uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug"]
        read_only_fields = ["created_at", "updated_at", "id", "uid", "slug"]


class BlockCreateUpdateSerializer(serializers.ModelSerializer):
    page = serializers.SlugRelatedField(slug_field="uid", queryset=Page.objects.only("uid", "first_block_id").all())
    next = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=Block.objects.select_related("previous").only("uid", "page_id", "previous__id").all(),
        allow_null=True,
    )

    class Meta:
        model = Block
        fields = ("page", "next", "content")

    def validate_page(self, page: Page) -> Page:
        if self.instance:
            raise serializers.ValidationError("Can't be sent in update requests.")
        return page

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        # In case of create, next will always be present, but in case of update, it may or may not be present
        if "next" in data:
            if self.instance:
                page: Page = self.instance.page
            else:
                page = data["page"]
            next: Block | None = data["next"]
            if next and next.page_id != page.pk:
                raise serializers.ValidationError("next block is in different page.")

            # Pop `next` if provided value is same as the current next.
            if self.instance and self.instance.next == next:
                data.pop("next")

        return data

    def create(self, validated_data: dict[str, Any]) -> Block:
        next = validated_data.pop("next", None)
        instance = super().create(validated_data)

        page = instance.page

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
        else:
            # If there are already existing blocks and the new block does not have a next pointer, it means that it
            # is the new last pointer. We need to set it as the next pointer of the previous last block.
            if page.first_block_id:
                Block.objects.filter(page_id=page.id, next_id__isnull=True).exclude(id=instance.id).update(
                    next_id=instance.id, updated_at=timezone.now()
                )

        if not page.first_block_id or (next and page.first_block_id == next.id):
            page.first_block_id = instance.id
            page.save(update_fields=["first_block_id", "updated_at"])

        return instance

    def update(self, instance: Block, validated_data: dict[str, Any]) -> Block:
        new_next = None
        new_previous = None
        blocked_moved = False
        if "next" in validated_data:
            blocked_moved = True
            new_next = validated_data["next"]
            if new_next:
                try:
                    new_previous = new_next.previous
                except Block.previous.RelatedObjectDoesNotExist:
                    pass

            cur_next = instance.next
            try:
                cur_previous = instance.previous
            except Block.previous.RelatedObjectDoesNotExist:
                cur_previous = None

        update_fields = {"updated_at"}
        to_update = []
        update_timestamp = timezone.now()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            update_fields.add(attr)
        instance.updated_at = update_timestamp
        to_update.append(instance)
        if blocked_moved:
            if new_previous:
                new_previous.next = instance
                new_previous.updated_at = update_timestamp
                to_update.append(new_previous)
            if cur_previous:
                cur_previous.next = cur_next
                cur_previous.updated_at = update_timestamp
                to_update.append(cur_previous)

        Block.objects.bulk_update(to_update, fields=update_fields)
        page: Page = instance.page
        if new_next and page.first_block_id == new_next.id:
            page.first_block_id = instance.id
            page.save(update_fields=["first_block_id", "updated_at"])
        elif blocked_moved and page.first_block_id == instance.id:
            page.first_block_id = cur_next.id
            page.save(update_fields=["first_block_id", "updated_at"])

        return instance
