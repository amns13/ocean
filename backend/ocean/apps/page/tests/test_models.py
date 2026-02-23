from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify
from factory import Iterator
from faker import Faker

from ocean.apps.page.models import Page
from ocean.apps.page.tests.factories import PageFactory

faker = Faker()


class TestPageModel(TestCase):
    def setUp(self):
        self.page = PageFactory()

    def test_str_returns_title(self):
        """Test that str returns title"""
        self.assertEqual(str(self.page), self.page.title)

    def test_save_slug_saved_corectly(self):
        """Test that save sets slug correctly"""
        self.page.title = faker.sentence()
        self.page.save()
        self.page.refresh_from_db()

        self.assertEqual(slugify(self.page.title), self.page.slug)

    def test_save_slug_saved_corectly_with_update_fields(self):
        """Test that save sets slug correctly when called with update fields"""
        self.page.title = faker.sentence()
        self.page.save(update_fields=["title"])
        self.page.refresh_from_db()

        self.assertEqual(slugify(self.page.title), self.page.slug)

    def test_save_with_update_fields_without_title_title_and_slug_not_updated(self):
        """Test that when save is called with updated fields not containing title, title and slug are not changed"""
        original_title = self.page.title
        original_slug = self.page.slug
        new_title = faker.sentence()
        self.page.title = new_title
        self.page.save(update_fields=["updated_at"])
        self.page.refresh_from_db()

        self.assertEqual(original_slug, self.page.slug)
        self.assertEqual(original_title, self.page.title)

    def test_delete_sets_deleted_at(self):
        """Test that delete method saves deleted_at"""
        self.page.delete()
        self.page.refresh_from_db()
        self.assertIsNotNone(self.page.deleted_at)

    def test_set_slug_trunctates_slug(self):
        """Test that set slug truncates slug if its length is more than 127"""
        value = "a" * 128
        self.assertEqual(len(value), 128)
        self.page.title = value
        self.page.set_slug()
        self.assertEqual(self.page.slug, "a" * 127)


class TestPageManager(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page, cls.deleted_page = PageFactory.create_batch(2, deleted_at=Iterator([None, timezone.now()]))

    def test_objects_returns_non_deleted_pages(self):
        """Test that objects returns only non-deleted pages"""
        pages = Page.objects.all()
        self.assertEqual(1, pages.count())
        self.assertListEqual(list(pages.values_list("id", flat=True)), [self.page.id])

    def test_all_objects_returns_deleted_and_non_deleted_pages(self):
        """Test that all_objects returns both deleted and non-deleted pages"""
        pages = Page.all_objects.all()
        self.assertEqual(2, pages.count())
        self.assertSetEqual(set(pages.values_list("id", flat=True)), {self.page.id, self.deleted_page.id})

    def test_queryset_delete_sets_deleted_at(self):
        """Test that queryset delete sets deleted_at"""
        Page.objects.all().delete()
        pages = Page.all_objects.all()
        self.assertEqual(2, pages.count())
        for page in pages:
            self.assertIsNotNone(page.deleted_at)
