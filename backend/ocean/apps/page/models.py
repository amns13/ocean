from uuid import uuid7

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from ocean.apps.page.managers import SoftDeleteManager

# from ocean.apps.page.managers import PageManager, BlockManager

User = get_user_model()


class Page(models.Model):
    uid = models.UUIDField(default=uuid7, unique=True)
    title = models.CharField(max_length=127, blank=False)
    slug = models.SlugField(max_length=127, blank=True)
    is_read_only = models.BooleanField(default=False)
    extra = models.JSONField(default=dict, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_pages")
    first_block = models.OneToOneField("Block", on_delete=models.SET_NULL, null=True, related_name="starts_page")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

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

    def delete(self):
        self.deleted_at = timezone.now()
        # TODO: Only update specific columns
        self.save()

    @property
    def last_block(self) -> "Block" | None:
        return self.blocks.filter(next__isnull=True).first()


class Block(models.Model):
    uid = models.UUIDField(default=uuid7, unique=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    content = models.TextField()
    # Django create OneToOneField as a ForeignKey with UniqueConstraint. This unique constraint in non_deferrable.
    # Now consider the scenario:
    # Blocks: A -> B -> C -> D
    # We want to move B to the position after D, i.e, new config: A -> C -> B -> D.
    # If we try to update all of A, B and C's next in one query, Postgres throws an error that unique constraint is
    # violated due to multiple blocks having B/C/D as next blocks, even though at the end of the query, uniqueness is maintained.
    # To handle this, we create an explicit deferred unique constraint from class.Meta and remove the implicit contraint.
    next = models.OneToOneField(
        "self", on_delete=models.SET_NULL, null=True, related_name="previous", db_constraint=False, db_index=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_block_next",
                fields=["next"],
                deferrable=models.Deferrable.DEFERRED,
            )
        ]


class PageAction(models.Model):
    class ActionType(models.TextChoices):
        VIEW = "view", "Viewed"
        CREATE = "create", "Created"
        EDIT = "edit", "Edited"
        DELETE = "delete", "Deleted"
        LOCK = "lock", "Locked"
        UNLOCK = "unlock", "Unlocked"

    page = models.ForeignKey(Page, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="actions")
    action = models.CharField(choices=ActionType, max_length=15)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.page_id} {self.get_action_value()} by {self.actor_id}"
