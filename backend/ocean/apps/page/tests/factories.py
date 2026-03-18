from uuid import uuid7

import factory
from django.utils.text import slugify
from factory.django import DjangoModelFactory

from ocean.apps.page.models import Block, Page
from ocean.apps.user.tests.factories import UserFactory


class PageFactory(DjangoModelFactory):
    class Meta:
        model = Page

    uid = factory.LazyFunction(uuid7)
    title = factory.Faker("sentence", nb_words=5)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    is_read_only = False
    extra = factory.LazyFunction(dict)
    creator = factory.SubFactory(UserFactory)
    deleted_at = None


class BlockFactory(DjangoModelFactory):
    class Meta:
        model = Block

    uid = factory.LazyFunction(uuid7)
    page = factory.SubFactory(PageFactory)
    content = factory.Faker("sentence", nb_words=5)
