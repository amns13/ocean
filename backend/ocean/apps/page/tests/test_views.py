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
        cls.block_1_a = BlockFactory(page=cls.page_1, index=1)
        cls.block_1_b = BlockFactory(page=cls.page_1, index=2)
        cls.block_1_c = BlockFactory(page=cls.page_1, index=3)

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

    def test_list_returns_all_pages(self):
        response = self.call_list_api(self.user_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.json(), [self.create_page_response(p) for p in [self.page_2, self.page_1]])

    def test_post_creates_new_page(self):
        data = {"title": faker.sentence()}
        response = self.call_post_api(data, self.user_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_page = Page.objects.filter(creator=self.user_1).exclude(id=self.page_1.id).get()
        self.assertDictEqual(response.json(), self.create_page_response(created_page))

    def test_blocks_returns_blocks_ordered_by_index(self):
        with self.assertNumQueries(2):
            # 1. query for fetching the page
            # 2. query for getting blocks list
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
    """
    Tests for BlockCreateUpdateDestroyViewSet covering create (POST), update (PATCH), and delete (DELETE).

    POST:
    - Test that post fails for unauthenticated request
    - Test that post fails when page field is missing
    - Test that post fails when page uid does not exist
    - Test that blocks can be created with empty content
    - Test that creating a block assigns index = max(existing) + 1
    - Test that creating the first block in a page assigns index 1

    PATCH:
    - Test that PUT is not allowed
    - Test that PATCH fails for unauthenticated request
    - Test that PATCH fails if page is provided
    - Test that PATCH updates content

    DELETE:
    - Test that DELETE fails for unauthenticated request
    - Test that DELETE returns 404 for a non-existent block
    - Test that DELETE removes the block
    """

    list_url = reverse("page:block-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_1, cls.page_2 = PageFactory.create_batch(2)
        cls.user = UserFactory()

    def setUp(self):
        self.block_1_a = BlockFactory(page=self.page_1, index=1)
        self.block_1_b = BlockFactory(page=self.page_1, index=2)
        self.block_1_c = BlockFactory(page=self.page_1, index=3)

        self.payload = {
            "page": self.page_1.uid,
            "content": faker.sentence(),
        }

    @staticmethod
    def get_detail_url(uid) -> str:
        return reverse("page:block-detail", kwargs={"uid": uid})

    def call_post_api(self, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.post(self.list_url, data, format="json")

    def call_patch_api(self, uid, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.patch(self.get_detail_url(uid), data, format="json")

    def call_put_api(self, uid, data, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.put(self.get_detail_url(uid), data, format="json")

    def call_delete_api(self, uid, user=None):
        if user:
            self.client.force_authenticate(user)
        return self.client.delete(self.get_detail_url(uid))

    @staticmethod
    def create_block_response(block: Block) -> dict:
        return {
            "uid": str(block.uid),
            "page": str(block.page.uid),
            "content": block.content,
        }

    # --- POST ---

    def test_post_fails_for_unauthenticated(self):
        """Test that post fails for unauthenticated request"""
        with self.assertNumQueries(0):
            response = self.call_post_api(self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_fails_if_page_not_provided(self):
        """Test that post fails when page field is missing"""
        self.payload.pop("page")

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": ["This field is required."]}, response.json())

    def test_post_fails_if_invalid_page_uid_provided(self):
        """Test that post fails when page uid does not exist"""
        while (invalid_uid := uuid7()) in {self.page_1.uid, self.page_2.uid}:
            continue
        self.payload["page"] = invalid_uid

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": [f"Object with uid={invalid_uid} does not exist."]}, response.json())

    def test_post_creates_block_with_empty_content(self):
        """Test that blocks can be created with empty content"""
        self.payload["content"] = ""

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_1, content="", index=4)
        self.assertDictEqual(self.create_block_response(new_block), response.json())

    def test_post_assigns_next_sequential_index(self):
        """Test that creating a block assigns index = max(existing) + 1"""
        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.assertEqual(new_block.index, 4)

    def test_post_first_block_in_page_assigns_index_1(self):
        """Test that creating the first block in a page assigns index 1"""
        response = self.call_post_api({"page": self.page_2.uid, "content": faker.sentence()}, self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        new_block = Block.objects.get(page=self.page_2)
        self.assertEqual(new_block.index, 1)

    # --- PATCH ---

    def test_put_is_not_allowed(self):
        """Test that PUT is not allowed"""
        response = self.call_put_api(self.block_1_b.uid, self.payload, self.user)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_fails_for_unauthenticated(self):
        """Test that PATCH fails for unauthenticated request"""
        response = self.call_patch_api(self.block_1_b.uid, {"content": faker.sentence()})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_fails_if_page_is_provided(self):
        """Test that PATCH fails if page is provided"""
        response = self.call_patch_api(self.block_1_b.uid, {"page": str(self.page_1.uid)}, self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())
        self.assertDictEqual({"page": ["Can't be sent in update requests."]}, response.json())

    def test_patch_updates_content(self):
        """Test that PATCH updates block content"""
        new_content = faker.sentence()

        response = self.call_patch_api(self.block_1_b.uid, {"content": new_content}, self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.block_1_b.refresh_from_db()
        self.assertDictEqual(self.create_block_response(self.block_1_b), response.json())
        self.assertEqual(self.block_1_b.content, new_content)

    # --- DELETE ---

    def test_delete_fails_for_unauthenticated(self):
        """Test that DELETE fails for unauthenticated request"""
        response = self.call_delete_api(self.block_1_b.uid)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_returns_404_for_nonexistent_block(self):
        """Test that DELETE returns 404 for a non-existent block"""
        while (invalid_uid := uuid7()) in set(Block.objects.values_list("uid", flat=True)):
            continue
        response = self.call_delete_api(invalid_uid, self.user)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_removes_block(self):
        """Test that DELETE removes the block"""
        response = self.call_delete_api(self.block_1_b.uid, self.user)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Block.objects.filter(uid=self.block_1_b.uid).exists())
