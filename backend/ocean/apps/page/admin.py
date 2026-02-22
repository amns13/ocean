from django.contrib import admin

from ocean.apps.page.models import Page, PageAction


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    exclude = ("deleted_at",)
    prepopulated_fields = {"slug": ["title"]}


@admin.register(PageAction)
class PageActionAdmin(admin.ModelAdmin):
    pass
