from unittest.mock import patch
from uuid import uuid7

from django.conf import settings
from django.urls import reverse
from factory import Iterator
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from ocean.apps.page.models import Block, Page
from ocean.apps.page.tests.factories import BlockFactory, PageFactory
from ocean.apps.user.tests.factories import UserFactory

faker = Faker()


class TestPageViewSet(APITestCase):
    list_url = reverse("page:page-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None
        cls.user_1, cls.user_2 = UserFactory.create_batch(2)
        cls.page_1, cls.page_2 = PageFactory.create_batch(2, creator=Iterator([cls.user_1, cls.user_2]))
        cls.block_1_a = BlockFactory(page=cls.page_1)
        cls.block_1_b = BlockFactory(page=cls.page_1, previous=cls.block_1_a)
        cls.block_1_a.next = cls.block_1_b
        cls.block_1_a.save()
        cls.block_1_a.refresh_from_db()
        cls.block_1_c = BlockFactory(page=cls.page_1, previous=cls.block_1_b)
        cls.block_1_b.next = cls.block_1_c
        cls.block_1_b.save()
        cls.block_1_b.refresh_from_db()

    @staticmethod
    def get_blocks_url(uid) -> str:
        return reverse("page:page-blocks", kwargs={"uid": uid})

    def call_list_api(self, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.get(self.list_url)

    def call_post_api(self, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.post(self.list_url, data, format="json")

    def call_blocks_api(self, uid, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.get(self.get_blocks_url(uid))

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

    def test_blocks_returns_blocks_in_correct_order(self):
        # 1. query for fetching the page
        # 2. query for getting blocks list
        with self.assertNumQueries(2):
            response = self.call_blocks_api(self.page_1.uid, self.user_1)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        expected_response = [
            {"uid": str(block.uid), "content": block.content}
            for block in [self.block_1_a, self.block_1_b, self.block_1_c]
        ]
        self.assertListEqual(expected_response, response.json())

    def test_blocks_returns_empty_if_no_blocks_in_page(self):
        response = self.call_blocks_api(self.page_2.uid, self.user_2)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([], response.json())


class TestBlockCreateUpdateDestroyViewSet(APITestCase):
    list_url = reverse("page:block-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_1, cls.page_2 = PageFactory.create_batch(2)
        cls.user = UserFactory()

    def setUp(self):
        self.block_1_a = BlockFactory(page=self.page_1)
        self.block_1_b = BlockFactory(page=self.page_1, previous=self.block_1_a)
        self.block_1_a.next = self.block_1_b
        self.block_1_a.save()
        self.block_1_a.refresh_from_db()
        self.block_1_c = BlockFactory(page=self.page_1, previous=self.block_1_b)
        self.block_1_b.next = self.block_1_c
        self.block_1_b.save()
        self.block_1_b.refresh_from_db()

        self.payload = {
            "page": self.page_1.uid,
            "content": faker.sentence(),
            "next": self.block_1_c.uid,
        }

    def call_post_api(self, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.post(self.list_url, data, format="json")

    @staticmethod
    def create_block_response(block: Block) -> dict:
        return {
            "uid": str(block.uid),
            "page": str(block.page.uid),
            "content": block.content,
            "next": str(block.next.uid) if block.next else None,
            "previous": str(block.previous.uid) if block.previous else None,
        }

    def test_post_fails_for_unauthenticated(self):
        response = self.call_post_api(self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_fails_if_page_is_not_provided(self):
        self.payload.pop("page")
        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": ["This field is required."]}, response.json())

    def test_post_fails_if_invalid_page_uid_provided(self):
        # Ideally, there won't be a duplicate.
        # Still, adding while clause to make sure of this.
        while (invalid_uid := uuid7()) in {self.page_1.uid, self.page_2.uid}:
            continue
        self.payload["page"] = invalid_uid
        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": ["Page not found."]}, response.json())

    def test_post_no_existing_block_in_page(self):
        self.payload["page"] = self.page_2.uid
        self.payload["next"] = None

        with self.assertNumQueries(5):
            # 1. Query for fetching page
            # 2. Query for fetching current last block
            # 3. Savepoint
            # 4. Query for inserting new block
            # 5. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        new_block = Block.objects.get(page=self.page_2)
        self.assertDictEqual(self.create_block_response(new_block), response.json())

    def test_post_existing_blocks_in_page_next_prev_not_provided_page_added_to_end(self):
        page = Page.objects.get(uid=self.payload["page"])
        original_last_block = page.last_block

        self.payload["next"] = None

        with self.assertNumQueries(6):
            # 1. Query for fetching page
            # 2. Query for fetching current last block
            # 3. Savepoint
            # 4. Query for inserting new block
            # 5. Query to bulk-update adjacent blocks' pointers
            # 6. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        page.refresh_from_db()
        new_block = page.last_block
        original_last_block.refresh_from_db()
        self.assertIsNone(new_block.next)
        self.assertEqual(original_last_block, new_block.previous)
        self.assertEqual(new_block, original_last_block.next)

    def test_post_fails_if_linked_blocks_not_found(self):
        self.payload["next"] = uuid7()  # non-existent UID

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("non_field_errors", response.json())

    def test_post_creates_block_in_middle(self):
        # Default payload inserts between block_1_b and block_1_c
        with self.assertNumQueries(6):
            # 1. Query for fetching page
            # 2. Query for fetching linked blocks
            # 3. Savepoint
            # 4. Query for inserting new block
            # 5. Query to bulk-update adjacent blocks' pointers
            # 6. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.assertDictEqual(self.create_block_response(new_block), response.json())

        self.block_1_b.refresh_from_db()
        self.block_1_c.refresh_from_db()
        self.assertEqual(self.block_1_b.next, new_block)
        self.assertEqual(self.block_1_c.previous, new_block)

    def test_post_creates_block_as_new_first(self):
        # block_1_a is the first block (previous=None)
        self.payload["next"] = self.block_1_a.uid

        with self.assertNumQueries(6):
            # 1. Query for fetching page
            # 2. Query for fetching linked blocks
            # 3. Savepoint
            # 4. Query for inserting new block
            # 5. Query to bulk-update adjacent block's pointer
            # 6. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.assertDictEqual(self.create_block_response(new_block), response.json())

        self.block_1_a.refresh_from_db()
        self.assertEqual(self.block_1_a.previous, new_block)

    def test_post_create_is_atomic(self):
        existing_blocks_count = Block.objects.filter(page__uid=self.payload["page"]).count()
        with patch.object(Block.objects, "bulk_update", side_effect=Exception("Simulated failure")):
            with self.assertRaises(Exception):
                self.call_post_api(self.payload, self.user)

        self.assertEqual(existing_blocks_count, Block.objects.filter(page__uid=self.payload["page"]).count())
