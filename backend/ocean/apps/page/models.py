from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

from ocean.apps.common.models import (
    CreateUpdateTimeStampModelMixin,
    SoftDeleteModelMixin,
    UidAndTimestampFieldModelMixin,
    UidFieldModelMixin,
)

User = get_user_model()


class Page(UidAndTimestampFieldModelMixin):
    title = models.CharField(max_length=127, blank=False)
    slug = models.SlugField(max_length=127, blank=True)
    is_read_only = models.BooleanField(default=False)
    extra = models.JSONField(default=dict, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_pages")

    def __str__(self) -> str:
        return self.title

    def set_slug(self):
        self.slug = slugify(self.title)[:127]

    def save(self, *args, **kwargs):
        if update_fields := kwargs.get("update_fields"):
            if "title" in update_fields:
                self.set_slug()
                update_fields.append("slug")
        else:
            self.set_slug()
        return super().save(*args, **kwargs)


class Block(UidAndTimestampFieldModelMixin):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    content = models.TextField(blank=True)
    index = models.IntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(name="unique_index_within_page", fields=["page", "index"])]

    def __str__(self) -> str:
        return f"{self.page_id}: Block {self.index}"


def _page_image_upload_path(instance: "Image", filename: str) -> str:
    return f"images/{instance.uploaded_by_id}/{instance.uid}/{filename}"


class Image(SoftDeleteModelMixin, UidFieldModelMixin):
    image = models.ImageField(upload_to=_page_image_upload_path)
    content_hash = models.CharField(max_length=64, unique=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_page_images")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.image.name


class PageImage(SoftDeleteModelMixin, CreateUpdateTimeStampModelMixin):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="instances")
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="images")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(name="unique_image_within_page", fields=["page", "image"])]
