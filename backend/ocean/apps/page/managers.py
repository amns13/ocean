from django.db import models
from django.utils import timezone


class PageQueryset(models.QuerySet):
    def all(self):
        return self.filter(deleted_at__isnull=True)

    def delete(self):
        return self.update(deleted_at=timezone.now())


class PageManager(models.Manager):
    def get_queryset(self):
        return PageQueryset(self.model, using=self._db)

    def all(self):
        return self.get_queryset().all()
