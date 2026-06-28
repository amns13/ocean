from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import AnyHttpUrl

from ocean.apps.page.models import Block, Page


class PageSchema(ModelSchema):
    class Meta:
        model = Page
        fields = ("uid", "title", "is_read_only", "created_at", "updated_at", "extra", "creator", "slug")


class PageSchemaIn(ModelSchema):
    class Meta:
        model = Page
        fields = ("title",)


class BlockSchemaIn(ModelSchema):
    class Meta:
        model = Block
        fields = ("content",)


class BlockSchemaOut(ModelSchema):
    class Meta:
        model = Block
        fields = ("uid", "content")


class BlockCreateSchemaIn(BlockSchemaOut):
    page: UUID


class BlockCreateSchemaOut(BlockSchemaOut):
    page: UUID

    @staticmethod
    def resolve_page(obj):
        return obj.page.uid


class UploadImageSchemaOut(Schema):
    image_url: AnyHttpUrl
