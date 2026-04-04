from django.contrib import admin

from ocean.apps.page.models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    exclude = ("deleted_at",)
    prepopulated_fields = {"slug": ["title"]}

