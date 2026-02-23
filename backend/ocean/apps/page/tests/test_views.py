from django.conf import settings
from django.urls import reverse
from factory import Iterator
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from ocean.apps.page.models import Page
from ocean.apps.page.tests.factories import PageFactory
from ocean.apps.user.tests.factories import UserFactory

faker = Faker()


class TestPageViewSet(APITestCase):
    url = reverse("page:page-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None
        cls.user_1, cls.user_2 = UserFactory.create_batch(2)
        cls.page_1, cls.page_2 = PageFactory.create_batch(2, creator=Iterator([cls.user_1, cls.user_2]))

    def call_list_api(self, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.get(self.url)

    def call_post_api(self, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.post(self.url, data, format="json")

    @staticmethod
    def create_page_response(page: Page) -> dict:
        return {
            "id": page.id,
            "uid": str(page.uid),
            "title": page.title,
            "slug": page.slug,
            "extra": page.extra,
            "creator": page.creator_id,
            "is_read_only": page.is_read_only,
            "created_at": page.created_at.strftime(settings.DRF_DATETIME_FORMAT),
            "updated_at": page.updated_at.strftime(settings.DRF_DATETIME_FORMAT),
        }

    def test_list_fails_for_unauthenticated(self):
        response = self.call_list_api()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_authored_pages(self):
        response = self.call_list_api(self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.json(), [self.create_page_response(self.page_1)])

    def test_post_creates_new_page(self):
        data = {"title": faker.sentence()}
        response = self.call_post_api(data, self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_page = Page.objects.filter(creator=self.user_1).exclude(id=self.page_1.id).get()
        self.assertDictEqual(response.json(), self.create_page_response(created_page))
