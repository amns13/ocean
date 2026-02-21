from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from ocean.apps.user.models import User

admin.site.register(User, UserAdmin)
