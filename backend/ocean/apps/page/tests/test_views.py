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
        # Create blocks in reverse order so that we do not have to update next later
        cls.block_1_c = BlockFactory(page=cls.page_1)
        cls.block_1_b = BlockFactory(page=cls.page_1, next=cls.block_1_c)
        cls.block_1_a = BlockFactory(page=cls.page_1, next=cls.block_1_b)
        cls.page_1.first_block = cls.block_1_a
        cls.page_1.save()
        cls.page_1.refresh_from_db()

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


class TestBlockCreateSerializer(APITestCase):
    """
    Tests for the new ModelSerializer-based BlockCreateSerializer.

    - Test that post fails for unauthenticated request
    - Test that post fails when page field is missing
    - Test that post fails when content field is missing
    - Test that post fails when page uid does not exist
    - Test that post fails when next uid does not exist
    - Test that post fails when next block belongs to a different page
    - Test that creating the first block in a page sets page.first_block
    - Test that inserting before the current first block updates page.first_block
    - Test that inserting in the middle rewires neighbours and leaves page.first_block unchanged
    - Test that appending to the end leaves page.first_block unchanged
    - Test that a failed bulk_update rolls back the entire block creation
    """

    list_url = reverse("page:block-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_1, cls.page_2 = PageFactory.create_batch(2)
        cls.user = UserFactory()

    def setUp(self):
        self.block_1_c = BlockFactory(page=self.page_1)
        self.block_1_b = BlockFactory(page=self.page_1, next=self.block_1_c)
        self.block_1_a = BlockFactory(page=self.page_1, next=self.block_1_b)
        self.page_1.first_block = self.block_1_a
        self.page_1.save()
        self.page_1.refresh_from_db()

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
        }

    def test_post_fails_for_unauthenticated(self):
        """ Test that post fails for unauthenticated request """
        with self.assertNumQueries(0):
            response = self.call_post_api(self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_fails_if_page_not_provided(self):
        """ Test that post fails when page field is missing """
        self.payload.pop("page")

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": ["This field is required."]}, response.json())

    def test_post_fails_if_content_not_provided(self):
        """ Test that post fails when content field is missing """
        self.payload.pop("content")

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"content": ["This field is required."]}, response.json())

    def test_post_fails_if_invalid_page_uid_provided(self):
        """ Test that post fails when page uid does not exist """
        while (invalid_uid := uuid7()) in {self.page_1.uid, self.page_2.uid}:
            continue
        self.payload["page"] = invalid_uid

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": [f"Object with uid={invalid_uid} does not exist."]}, response.json())

    def test_post_fails_if_invalid_next_uid_provided(self):
        """ Test that post fails when next uid does not exist """
        while (invalid_uid := uuid7()) in set(Block.objects.values_list("uid", flat=True)):
            continue
        self.payload["next"] = invalid_uid

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"next": [f"Object with uid={invalid_uid} does not exist."]}, response.json())

    def test_post_fails_if_next_block_is_from_different_page(self):
        """ Test that post fails when next block belongs to a different page """
        other_page_block = BlockFactory(page=self.page_2)
        self.payload["next"] = other_page_block.uid

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"non_field_errors": ["next block is in different page."]}, response.json())

    def test_post_first_block_in_page_sets_page_first_block(self):
        """ Test that creating the first block in a page sets page.first_block """
        # page_2 has no blocks yet
        with self.assertNumQueries(5):
            # 1. SlugRelatedField resolves `page` (page_2)
            # 2. Savepoint
            # 3. INSERT new block
            # 4. page.save() — page_2.first_block was None, so it's updated
            # 5. Release savepoint
            # (`next` is None — SlugRelatedField skips the DB lookup)
            response = self.call_post_api(
                {"page": self.page_2.uid, "content": faker.sentence(), "next": None}, self.user
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_2)
        self.page_2.refresh_from_db()
        self.assertEqual(self.page_2.first_block, new_block)
        self.assertIsNone(new_block.next)

    def test_post_insert_before_first_block_updates_page_first_block(self):
        """ Test that inserting before the current first block updates page.first_block """
        # next=block_1_a means the new block becomes the new head of the list
        self.payload["next"] = self.block_1_a.uid

        with self.assertNumQueries(7):
            # 1. SlugRelatedField resolves `page`
            # 2. SlugRelatedField resolves `next` and select related previous
            # 3. Savepoint
            # 4. INSERT new block
            # 5. bulk_update new block's next pointer
            # 6. page.save() — new block is now the head, first_block updated
            # 7. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.page_1.refresh_from_db()
        self.assertEqual(self.page_1.first_block, new_block)
        self.assertEqual(new_block.next, self.block_1_a)

    def test_post_insert_in_middle_rewires_adjacent_blocks(self):
        """ Test that inserting in the middle rewires neighbours and leaves page.first_block unchanged """
        # Default payload inserts between block_1_b and block_1_c
        with self.assertNumQueries(6):
            # 1. SlugRelatedField resolves `page`
            # 2. SlugRelatedField resolves `next` (block_1_c)
            # 3. Savepoint
            # 4. INSERT new block
            # 5. bulk_update block_1_b.next and new block's next
            # 6. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])

        self.block_1_b.refresh_from_db()
        self.assertEqual(self.block_1_b.next, new_block)
        self.assertEqual(new_block.next, self.block_1_c)
        # Assert that page's first_block is unchanged
        self.page_1.refresh_from_db()
        self.assertEqual(self.page_1.first_block, self.block_1_a)

    def test_post_insert_as_last_block_does_not_change_page_first_block(self):
        """ Test that appending to the end leaves page.first_block unchanged """
        # next=None — block appended to the end
        self.payload["next"] = None

        with self.assertNumQueries(4):
            # 1. SlugRelatedField resolves `page`
            # 2. Savepoint
            # 3. INSERT new block
            # 4. Release savepoint
            response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.assertIsNone(new_block.next)

        self.page_1.refresh_from_db()
        self.assertEqual(self.page_1.first_block, self.block_1_a)

    def test_post_create_is_atomic(self):
        """ Test that a failed bulk_update rolls back the entire block creation """
        existing_blocks_count = Block.objects.filter(page=self.page_1).count()
        with patch.object(Block.objects, "bulk_update", side_effect=Exception("Simulated failure")):
            with self.assertRaises(Exception):
                self.call_post_api(self.payload, self.user)

        self.assertEqual(existing_blocks_count, Block.objects.filter(page=self.page_1).count())
        self.page_1.refresh_from_db()
        self.assertEqual(self.page_1.first_block, self.block_1_a)
