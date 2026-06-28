import hashlib
import logging
from uuid import UUID

from django.conf import settings
from django.db.models import Max
from django.http import FileResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from ninja import File, Router, Status
from ninja.errors import ValidationError
from ninja.files import UploadedFile
from ninja.security import SessionAuth

from ocean.apps.page.models import Block, Image, Page, PageImage
from ocean.apps.page.schemas import (
    BlockCreateSchemaIn,
    BlockCreateSchemaOut,
    BlockSchemaIn,
    BlockSchemaOut,
    PageSchema,
    PageSchemaIn,
    UploadImageSchemaOut,
)

router = Router(auth=SessionAuth())
logger = logging.getLogger(__name__)

PAGE_LIST_URL = "/pages/"
PAGE_DETAILS_URL = "/pages/{uuid:uid}/"
BLOCK_LIST_URL = "/blocks/"
BLOCK_DETAILS_URL = "/blocks/{uuid:uid}/"


@router.get(PAGE_LIST_URL, response=list[PageSchema])
def list_pages(request: HttpRequest):
    queryset = Page.objects.order_by("-id")
    return queryset


@router.post(PAGE_LIST_URL, response={201: PageSchema})
def create_page(request: HttpRequest, data: PageSchemaIn):
    return Page.objects.create(**data.dict(), creator=request.user)


@router.get(PAGE_DETAILS_URL, response=PageSchema)
def retreive_page(request: HttpRequest, uid: UUID):
    return get_object_or_404(Page, uid=uid)


@router.put(PAGE_DETAILS_URL, response=PageSchema)
def update_page(request: HttpRequest, uid: UUID, data: PageSchemaIn):
    page = get_object_or_404(Page, uid=uid)
    update_fields = []
    for attr, value in data.dict().items():
        setattr(page, attr, value)
        update_fields.append(attr)
    update_fields.append("updated_at")
    page.save(update_fields=list(data.dict().keys()) + ["updated_at"])
    return page


@router.delete(PAGE_DETAILS_URL, response={204: None})
def delete_page(request: HttpRequest, uid: UUID):
    page = get_object_or_404(Page, uid=uid)
    page.delete()
    return Status(204, None)


@router.get(PAGE_DETAILS_URL + "blocks/", response=list[BlockSchemaOut])
def page_blocks(request: HttpRequest, uid: UUID):
    page = get_object_or_404(Page.objects.only("id", "uid"), uid=uid)
    return page.blocks.order_by("index").only("uid", "content", "page_id")


@router.post(BLOCK_LIST_URL, response={201: BlockCreateSchemaOut})
def create_block(request: HttpRequest, data: BlockCreateSchemaIn):
    try:
        page = Page.objects.annotate(last_block_index=Max("blocks__index")).only("uid", "id").get(uid=data.page)
    except Page.DoesNotExist:
        raise ValidationError(
            [{"loc": ("body", "data", "page"), "msg": f"Page with uid {data.page} not found", "type": "missing"}]
        )

    block_data = data.dict()
    block_data["page"] = page
    block_data["index"] = page.last_block_index + 1 if page.last_block_index else 1
    block = Block.objects.create(**block_data)
    return block


@router.patch(BLOCK_DETAILS_URL, response=BlockCreateSchemaOut)
def update_block(request: HttpRequest, uid: UUID, data: BlockSchemaIn):
    block: Block = get_object_or_404(Block.objects.select_related("page").only("id", "uid", "page__uid"), uid=uid)
    update_fields = []
    for attr, value in data.dict().items():
        setattr(block, attr, value)
        update_fields.append(attr)

    update_fields.append("updated_at")
    block.save(update_fields=list(data.dict().keys()) + ["updated_at"])
    return block


@router.delete(BLOCK_DETAILS_URL, response={204: None})
def delete_block(request: HttpRequest, uid: UUID):
    block: Block = get_object_or_404(Block, uid=uid)
    block.delete()
    return Status(204, None)


@router.post(PAGE_DETAILS_URL + "upload-image/", response=UploadImageSchemaOut)
def upload_image(request: HttpRequest, uid: UUID, image: File[UploadedFile]):
    page = get_object_or_404(Page.objects.only("id", "uid"), uid=uid)
    content_hash = hashlib.file_digest(image, "sha256").hexdigest()
    _image, created = Image.objects.get_or_create(
        content_hash=content_hash, defaults={"uploaded_by_id": request.user.id, "image": image}
    )

    if created:
        logger.info("Uploading new image. | Page id: %s | Content hash: %s", page.uid, content_hash)
        # If image is newly created, then we are sure that existing mappings don't exist.
        PageImage.objects.create(image=_image, page=page, user=request.user, name=image.name)
    else:
        logger.info("Image already exists. | Page id: %s | Content hash: %s", page.uid, content_hash)
        PageImage.objects.get_or_create(image=_image, page=page, defaults={"user": request.user, "name": image.name})

    return {
        "image_url": f"{settings.API_DOMAIN_PREFIX}{reverse('api-1:page-image-download', kwargs={'page_uid': page.uid, 'image_uid': _image.uid})}"
    }


@router.get("/pages/{uuid:page_uid}/download-image/{uuid:image_uid}/", url_name="page-image-download")
def download_image(request: HttpRequest, page_uid: UUID, image_uid: UUID):
    page_image = get_object_or_404(PageImage.objects.select_related("image"), page__uid=page_uid, image__uid=image_uid)
    return FileResponse(page_image.image.image.file.open("rb"), filename=page_image.name, as_attachment=False)
