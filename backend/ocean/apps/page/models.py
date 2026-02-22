from uuid import uuid7

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from ocean.apps.page.managers import PageManager

User = get_user_model()


class Page(models.Model):
    uid = models.UUIDField(default=uuid7)
    title = models.CharField(max_length=127, blank=False)
    slug = models.SlugField(max_length=127, blank=True)
    is_read_only = models.BooleanField(default=False)
    extra = models.JSONField(default=dict, blank=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_pages")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = PageManager()
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


class Block(models.Model):
    uid = models.UUIDField(default=uuid7)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    content = models.TextField()
    next = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, related_name="prev")


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
