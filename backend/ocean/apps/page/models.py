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
    def first_block(self) -> "Block" | None:
        return self.blocks.filter(previous__isnull=True).first()

    @property
    def last_block(self) -> "Block" | None:
        return self.blocks.filter(next__isnull=True).first()


class Block(models.Model):
    uid = models.UUIDField(default=uuid7, unique=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    content = models.TextField()
    next = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, related_name="previous_block")
    previous = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, related_name="next_block")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        constraints = [
            # Reason for keeping nulls_distinct = True?
            # When 1st block is created, its next is obviouly null. Now, when the 2nd block is created its next
            # will also be null and after its creation, we will set 1st block's next to point to the 2nd block.
            # So, during that time, we can't avoid having 2 blocks that have null as their next pointer.
            # THIS MUST BE HANDLED IN THE INSERTION LOGIC.
            # For previous pointer, similar logic applies if we add a new block before the 1st block.
            models.UniqueConstraint(name="page_next_unique_together", fields=["page", "next"], nulls_distinct=True),
            models.UniqueConstraint(
                name="page_previous_unique_together", fields=["page", "previous"], nulls_distinct=True
            ),
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
