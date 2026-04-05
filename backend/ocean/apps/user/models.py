from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from ocean.apps.common.models import UidFieldModelMixin


class User(AbstractUser, UidFieldModelMixin):
    email = models.EmailField(_("email address"), blank=False, unique=True)

    def __str__(self) -> str:
        return self.username
