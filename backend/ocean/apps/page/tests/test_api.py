from ocean.utils.testutils import ApiTestCase
from django.contrib.auth import get_user_model
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from factory import Iterator
from faker import Faker

from ocean.apps.page.models import Block, Page
from ocean.apps.page.tests.factories import BlockFactory, PageFactory
from ocean.apps.user.tests.factories import UserFactory

faker = Faker()
User = get_user_model()


class TestPageCreateListUpdateBlocksApis(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1, cls.user_2 = UserFactory.create_batch(2)
        cls.page_1, cls.page_2 = PageFactory.create_batch(2, creator=Iterator([cls.user_1, cls.user_2]))
        cls.block_1_a = BlockFactory(page=cls.page_1, index=1)
        cls.block_1_b = BlockFactory(page=cls.page_1, index=2)
        cls.block_1_c = BlockFactory(page=cls.page_1, index=3)

    def call_list_api(self, user=None):
        return self.call_api("get", "/pages/", user=user)

    def call_post_api(self, data, user=None):
        return self.call_api("post", "/pages/", user=user, json=data)

    def call_retreive_api(self, uid, user=None):
        return self.call_api("get", f"/pages/{uid}/", user=user)

    def call_blocks_api(self, uid, user=None):
        return self.call_api("get", f"/pages/{uid}/blocks/", user=user)

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
        self.assertEqual(response.status_code, 401)

    def test_list_returns_all_pages(self):
        with self.assertNumQueries(1):
            # 1. query for fetching pages
            response = self.call_list_api(self.user_1)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), [self.create_page_response(p) for p in [self.page_2, self.page_1]])

    def test_post_fails_for_unauthenticated_request(self):
        data = {"title": faker.sentence()}
        response = self.call_post_api(data)
        self.assertEqual(response.status_code, 401)

    def test_post_creates_new_page(self):
        data = {"title": faker.sentence()}
        response = self.call_post_api(data, self.user_1)
        self.assertEqual(response.status_code, 201)
        created_page = Page.objects.filter(creator=self.user_1).exclude(id=self.page_1.id).get()
        self.assertDictEqual(response.json(), self.create_page_response(created_page))

    def test_retreive_fails_for_unauthenticated_request(self):
        response = self.call_retreive_api(self.page_1.uid)
        self.assertEqual(401, response.status_code)

    def test_retreive_returns_404_for_invalid_uid(self):
        response = self.call_retreive_api(faker.uuid4(), self.user_1)
        self.assertEqual(404, response.status_code)

    def test_retreive_returns_correct_data_for_valid_uid(self):
        with self.assertNumQueries(1):
            # 1. query to fetch page
            response = self.call_retreive_api(self.page_1.uid, self.user_1)
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.create_page_response(self.page_1), response.json())

    def test_blocks_returns_401_for_unauthenticated_request(self):
        response = self.call_blocks_api(self.page_1.uid)
        self.assertEqual(401, response.status_code)

    def test_blocks_returns_404_for_invalid_uid(self):
        response = self.call_retreive_api(faker.uuid4(), self.user_1)
        self.assertEqual(404, response.status_code)

    def test_blocks_returns_blocks_ordered_by_index(self):
        with self.assertNumQueries(2):
            # 1. query for fetching the page
            # 2. query for getting blocks list
            response = self.call_blocks_api(self.page_1.uid, self.user_1)
        self.assertEqual(200, response.status_code)
        expected_response = [
            {"uid": str(block.uid), "content": block.content}
            for block in [self.block_1_a, self.block_1_b, self.block_1_c]
        ]
        self.assertListEqual(expected_response, response.json())

    def test_blocks_returns_empty_if_no_blocks_in_page(self):
        response = self.call_blocks_api(self.page_2.uid, self.user_2)
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())


class TestBlockCreateUpdateDeleteApis(ApiTestCase):
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

    def call_post_api(self, data, user=None):
        return self.call_api("post", "/pages/blocks/", user=user, json=data)

    def call_patch_api(self, uid, data, user=None):
        return self.call_api("patch", f"/pages/blocks/{uid}/", user=user, json=data)

    def call_put_api(self, uid, data, user=None):
        return self.call_api("put", f"/pages/blocks/{uid}/", user=user, json=data)

    def call_delete_api(self, uid, user=None):
        return self.call_api("delete", f"/pages/blocks/{uid}/", user=user)

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
        self.assertEqual(response.status_code, 401)

    def test_post_fails_if_page_not_provided(self):
        """Test that post fails when page field is missing"""
        self.payload.pop("page")

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, 422, response.json())
        self.assertEqual("Field required", response.json()["detail"][0]["msg"])
        self.assertListEqual(["body", "data", "page"], response.json()["detail"][0]["loc"])

    def test_post_fails_if_invalid_page_uid_provided(self):
        """Test that post fails when page uid does not exist"""
        self.payload["page"] = faker.uuid4()

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, 422, response.json())
        self.assertListEqual(["body", "data", "page"], response.json()["detail"][0]["loc"])
        self.assertEqual(f"Page with uid {self.payload['page']} not found", response.json()["detail"][0]["msg"])

    def test_post_creates_block_with_empty_content(self):
        """Test that blocks can be created with empty content"""
        self.payload["content"] = ""

        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, 201, response.json())
        new_block = Block.objects.get(page=self.page_1, content="", index=4)
        self.assertDictEqual(self.create_block_response(new_block), response.json())

    def test_post_assigns_next_sequential_index(self):
        """Test that creating a block assigns index = max(existing) + 1"""
        response = self.call_post_api(self.payload, self.user)

        self.assertEqual(response.status_code, 201, response.json())
        new_block = Block.objects.get(page=self.page_1, content=self.payload["content"])
        self.assertEqual(new_block.index, 4)

    def test_post_first_block_in_page_assigns_index_1(self):
        """Test that creating the first block in a page assigns index 1"""
        response = self.call_post_api({"page": self.page_2.uid, "content": faker.sentence()}, self.user)

        self.assertEqual(response.status_code, 201, response.json())
        new_block = Block.objects.get(page=self.page_2)
        self.assertEqual(new_block.index, 1)

    # --- PATCH ---

    def test_put_is_not_allowed(self):
        """Test that PUT is not allowed"""
        response = self.call_put_api(self.block_1_b.uid, self.payload, self.user)
        self.assertEqual(response.status_code, 405)

    def test_patch_fails_for_unauthenticated(self):
        """Test that PATCH fails for unauthenticated request"""
        response = self.call_patch_api(self.block_1_b.uid, {"content": faker.sentence()})
        self.assertEqual(response.status_code, 401)

    def test_patch_updates_content(self):
        """Test that PATCH updates block content"""
        new_content = faker.sentence()

        response = self.call_patch_api(self.block_1_b.uid, {"content": new_content}, self.user)

        self.assertEqual(response.status_code, 200, response.json())
        self.block_1_b.refresh_from_db()
        self.assertDictEqual(self.create_block_response(self.block_1_b), response.json())
        self.assertEqual(self.block_1_b.content, new_content)

    # --- DELETE ---

    def test_delete_fails_for_unauthenticated(self):
        """Test that DELETE fails for unauthenticated request"""
        response = self.call_delete_api(self.block_1_b.uid)
        self.assertEqual(response.status_code, 401)

    def test_delete_returns_404_for_nonexistent_block(self):
        """Test that DELETE returns 404 for a non-existent block"""
        while (invalid_uid := uuid4()) in set(Block.objects.values_list("uid", flat=True)):
            continue
        response = self.call_delete_api(invalid_uid, self.user)
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_block(self):
        """Test that DELETE removes the block"""
        response = self.call_delete_api(self.block_1_b.uid, self.user)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Block.objects.filter(uid=self.block_1_b.uid).exists())


class TestPageImageUploadDownloadApis(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_1, cls.page_2 = PageFactory.create_batch(2)
        cls.user = UserFactory()
        cls.image_path = settings.BASE_DIR / "ocean/apps/page/tests/fixtures/sample_image.png"

    def call_upload_api(self, uid, data, user: User | None = None):
        return self.call_api("post", f"/pages/{uid}/upload-image/", user=user, FILES=data)

    def call_download_api(self, page_uid, image_uid, user):
        return self.call_api("get", f"/pages/{page_uid}/download-image/{image_uid}/", user=user)

    def test_page_image_upload_raises_401_on_unauthorized_request(self):
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(str(self.page_1.uid), {"image": image})

        self.assertEqual(response.status_code, 401, response.json())

    def test_page_image_upload_raises_404_when_page_does_not_exist(self):
        invalid_uid = uuid4()

        with open(self.image_path, "rb") as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(invalid_uid, {"image": image}, self.user)

        self.assertEqual(response.status_code, 404, response.json())

    def test_page_image_upload_creates_new_image_on_new_request_with_unique_image(self):
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            with self.assertNumQueries(6):
                # 1. Query to fetch page
                # 2. Query to check for existing image
                # 3. Query to create save point
                # 4. Query to insert new image
                # 5. Query to Release save point
                # 6. Query to insert PageImage
                response = self.call_upload_api(str(self.page_1.uid), {"image": image}, self.user)

        self.assertEqual(response.status_code, 200)
        page_image_mappings = self.page_1.images.all()
        self.assertEqual(1, page_image_mappings.count())
        page_image_mapping = page_image_mappings.first()
        self.assertEqual(Path(self.image_path).name, page_image_mapping.name)
        image = page_image_mapping.image
        self.assertEqual(
            settings.API_DOMAIN_PREFIX
            + reverse(
                "api-1:page-image-download",
                kwargs={"page_uid": str(self.page_1.uid), "image_uid": str(image.uid)},
            ),
            response.json()["image_url"],
        )
        with open(image.image.path) as fp:
            contents = fp.read()

        with open(self.image_path) as fp:
            self.assertEqual(contents, fp.read())

    def test_page_image_upload_skips_duplicate_images_but_creates_mapping_if_page_is_new(self):
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(str(self.page_1.uid), {"image": image}, self.user)
        self.assertEqual(response.status_code, 200)
        page_image_mappings = self.page_1.images.all()
        self.assertEqual(1, page_image_mappings.count())
        page_image_mapping = page_image_mappings.first()
        original_image = page_image_mapping.image

        with open(self.image_path) as fsrc:
            with tempfile.NamedTemporaryFile(prefix="another_image", delete_on_close=False) as fdst:
                shutil.copyfileobj(fsrc, fdst)
                dest_file = fdst.name

                with open(dest_file) as fp:
                    duplicate_image = SimpleUploadedFile(dest_file, fp.read(), content_type="image/png")
                    with self.assertNumQueries(6):
                        # 1. Query to fetch page
                        # 2. Query to check for existing image
                        # 3. Query to check for existing PageImage mapping
                        # 4. Create savepoint
                        # 5. Query to insert PageImage
                        # 6. Release savepoint
                        response = self.call_upload_api(str(self.page_2.uid), {"image": duplicate_image}, self.user)

        self.assertEqual(response.status_code, 200)
        new_page_image_mappings = self.page_2.images.all()
        self.assertEqual(1, new_page_image_mappings.count())
        new_page_image_mapping = new_page_image_mappings.first()
        self.assertEqual(Path(dest_file).name, new_page_image_mapping.name)
        self.assertEqual(original_image.id, new_page_image_mapping.image.id)
        self.assertEqual(
            settings.API_DOMAIN_PREFIX
            + reverse(
                "api-1:page-image-download",
                kwargs={"page_uid": str(self.page_2.uid), "image_uid": str(original_image.uid)},
            ),
            response.json()["image_url"],
        )

    def test_page_image_upload_skips_both_image_and_mapping_creation_if_existing_image_is_added_to_same_page(self):
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(str(self.page_1.uid), {"image": image}, self.user)
        self.assertEqual(response.status_code, 200)
        page_image_mappings = self.page_1.images.all()
        self.assertEqual(1, page_image_mappings.count())
        page_image_mapping = page_image_mappings.first()
        original_image = page_image_mapping.image

        with open(self.image_path) as fsrc:
            with tempfile.NamedTemporaryFile(prefix="another_image", delete_on_close=False) as fdst:
                shutil.copyfileobj(fsrc, fdst)
                dest_file = fdst.name

                with open(dest_file) as fp:
                    duplicate_image = SimpleUploadedFile(dest_file, fp.read(), content_type="image/png")
                    with self.assertNumQueries(3):
                        # 1. Query to fetch page
                        # 2. Query to check for existing image
                        # 3. Query to check for existing PageImage mapping
                        response = self.call_upload_api(str(self.page_1.uid), {"image": duplicate_image}, self.user)

        self.assertEqual(response.status_code, 200)
        new_page_image_mappings = self.page_1.images.all()
        self.assertEqual(1, new_page_image_mappings.count())
        self.assertEqual(
            settings.API_DOMAIN_PREFIX
            + reverse(
                "api-1:page-image-download",
                kwargs={"page_uid": str(self.page_1.uid), "image_uid": str(original_image.uid)},
            ),
            response.json()["image_url"],
        )

    def test_page_image_download_raises_401_for_unauthenticated_request(self):
        # Upload the image first
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(str(self.page_1.uid), {"image": image}, self.user)
        self.assertEqual(response.status_code, 200)

        image_url = response.json()["image_url"]

        # Now, download.
        self.client.logout()
        response = self.client.get(image_url)
        self.assertEqual(401, response.status_code)

    def test_page_image_download_raises_404_if_page_does_not_exist(self):
        response = self.call_download_api(str(uuid4()), str(uuid4()), self.user)
        self.assertEqual(404, response.status_code)

    def test_page_image_download_raises_404_if_image_does_not_exist(self):
        response = self.call_download_api(str(self.page_1.uid), str(uuid4()), self.user)
        self.assertEqual(404, response.status_code)

    def test_page_image_download_returns_image_for_valid_request(self):
        # Upload the image first
        with open(self.image_path) as fp:
            image = SimpleUploadedFile("sample_image.png", fp.read(), content_type="image/png")
            response = self.call_upload_api(str(self.page_1.uid), {"image": image}, self.user)
        self.assertEqual(response.status_code, 200)

        image_url = response.json()["image_url"]

        # Now, download.
        self.client.force_login(self.user)
        response = self.client.get(image_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(Path(self.image_path).name, response.filename)
