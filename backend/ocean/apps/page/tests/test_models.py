import pytest
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from ocean.apps.page.models import Page
from ocean.apps.page.tests.factories import PageFactory

faker = Faker()


@pytest.fixture
def page(db):
    return PageFactory()


@pytest.mark.django_db
class TestPageModel:
    def test_str_returns_title(self, page):
        """Test that str returns title"""
        assert str(page) == page.title

    def test_save_slug_saved_corectly(self, page):
        """Test that save sets slug correctly"""
        page.title = faker.sentence()
        page.save()
        page.refresh_from_db()

        assert slugify(page.title) == page.slug

    def test_save_slug_saved_corectly_with_update_fields(self, page):
        """Test that save sets slug correctly when called with update fields"""
        page.title = faker.sentence()
        page.save(update_fields=["title"])
        page.refresh_from_db()

        assert slugify(page.title) == page.slug

    def test_save_with_update_fields_without_title_title_and_slug_not_updated(self, page):
        """Test that when save is called with updated fields not containing title, title and slug are not changed"""
        original_title = page.title
        original_slug = page.slug
        new_title = faker.sentence()
        page.title = new_title
        page.save(update_fields=["updated_at"])
        page.refresh_from_db()

        assert original_slug == page.slug
        assert original_title == page.title

    def test_delete_sets_deleted_at(self, page):
        """Test that delete method saves deleted_at"""
        page.delete()
        page.refresh_from_db()
        assert page.deleted_at is not None

    def test_set_slug_trunctates_slug(self, page):
        """Test that set slug truncates slug if its length is more than 127"""
        value = "a" * 128
        assert len(value) == 128
        page.title = value
        page.set_slug()
        assert page.slug == "a" * 127


class TestPageManager:
    def test_objects_returns_non_deleted_pages(self, page):
        """Test that objects returns only non-deleted pages"""
        PageFactory(deleted_at=timezone.now())
        pages = Page.objects.all()
        assert pages.count() == 1
        assert list(pages.values_list("id", flat=True)) == [page.id]

    def test_all_objects_returns_deleted_and_non_deleted_pages(self, page):
        """Test that all_objects returns both deleted and non-deleted pages"""
        deleted_page = PageFactory(deleted_at=timezone.now())
        pages = Page.all_objects.all()
        assert pages.count() == 2
        assert set(pages.values_list("id", flat=True)) == {page.id, deleted_page.id}

    def test_queryset_delete_sets_deleted_at(self, page):
        """Test that queryset delete sets deleted_at"""
        PageFactory()
        Page.objects.all().delete()
        pages = Page.all_objects.all()
        assert pages.count() == 2
        for page in pages:
            assert page.deleted_at is not None
