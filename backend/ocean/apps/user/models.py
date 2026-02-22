from uuid import uuid7
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    uid = models.UUIDField(default=uuid7)
    email = models.EmailField(_("email address"), blank=False, unique=True)

    def __str__(self) -> str:
        return self.username
