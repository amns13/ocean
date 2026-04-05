"""Abstract model mixins and custom managers and querysets providing common fields and functionalities for Ocean models.
Classes:
    SoftDeleteQueryset: Overrides Django's default QuerySet class to add soft deletion functionalities.
    SoftDeleteManager: Overrides Django's default Model Manager class to add soft deletion functionalities.
    UidFieldModelMixin: adds a uuid4 `uid` field.
    CreateUpdateTimeStampModelMixin: adds `created_at` / `updated_at` timestamps.
    SoftDeleteModelMixin: adds `deleted_at` and swaps in the soft-delete manager.
    UidAndTimestampFieldModelMixin: convenience composite of all three.
"""

from uuid import uuid4

from django.db import models
from django.utils import timezone


class SoftDeleteQueryset(models.QuerySet):
    """Custom Queryset class to support filtering out soft deleted rows by default.

    Django used `_deferred_filter` to apply filters in Queryset._filter_or_exclude method. By adding
    a default value, we force it to apply the default filtering everytime.

    TODO: Currently, multiple `deleted_at is null` conditions are being added to the query. Fix this.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deferred_filter = False, [], {"deleted_at__isnull": True}

    def delete(self) -> None:
        """Updates the deleted_at attribute to signal soft deletion.

        This does not take care of cascades and that is the user's responsibility.
        """
        self.update(deleted_at=timezone.now())


class SoftDeleteManager(models.Manager):
    """Custom manager for supporting soft deletion.

    Uses SoftDeleteQueryset as the queryset handler.
    """

    def get_queryset(self):
        return SoftDeleteQueryset(self.model, using=self._db)

    def all(self):
        return self.get_queryset().all()


class UidFieldModelMixin(models.Model):
    """Adds a globally unique uid field to the model.

    Uses UUIDv4 instead of UUIDv7 because it is truly random at the cost of index locality. UUIDv7 can leak
    the timestamp. Since this is the client facing key, we do not want to expose any kind of metadata.

    Attributes:
        uid: A unique id column
    """

    uid = models.UUIDField(default=uuid4, unique=True)

    class Meta:
        abstract = True


class CreateUpdateTimeStampModelMixin(models.Model):
    """Adds auto-managed `created_at` and `updated_at` timestamp fields.

    It is the user's responsibility to update these columns value when running operations that do not trigger
    auto_now or auto_now_add. This includes `update`, `bulk_update`, `bulk_create` etc.

    Attributes:
        created_at: Creation timestamp
        updated_at: Last update timestamp.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModelMixin(models.Model):
    """Adds soft-delete behaviour via a nullable `deleted_at` timestamp.

    Attributes:
        deleted_at: Deletion timestamp
        objects: Default manager that excludes any rows that are soft deleted from the query resultset.
        all_objects: Additional manager that returns all rows
    """

    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self) -> None:
        """
        Overrides the model's delete method to update the deleted_at field instead of performing a delete query
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class UidAndTimestampFieldModelMixin(UidFieldModelMixin, CreateUpdateTimeStampModelMixin, SoftDeleteModelMixin):
    """Composite mixin: uid + timestamps + soft-delete."""

    class Meta:
        abstract = True
