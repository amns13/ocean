from django.db import models
from django.utils import timezone


class PageQueryset(models.QuerySet):
    def non_deleted(self):
        self.filter(deleted_at__isnull=True)

    def delete(self):
        self.update(deleted_at=timezone.now())


class PageManager(models.Manager):
    def get_queryset(self):
        return PageQueryset(self.model, using=self._db)
