from django.db import models
from django.utils import timezone


class SoftDeleteQueryset(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deferred_filter = False, [], {"deleted_at__isnull": True}

    def delete(self):
        return self.update(deleted_at=timezone.now())


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQueryset(self.model, using=self._db)

    def all(self):
        return self.get_queryset().all()
