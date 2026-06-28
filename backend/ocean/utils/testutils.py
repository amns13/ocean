from django.contrib.auth import get_user_model
from django.test import TestCase
from ninja.testing.client import TestClient

from ocean.api import api

User = get_user_model()


class ApiTestCase(TestCase):
    """Custom test class that provides utility method to call apis using django-ninja's api client."""

    @staticmethod
    def call_api(method: str, url: str, user: User, *args, **kwargs):
        ninja_client = TestClient(api)
        _method = getattr(ninja_client, method)
        if user:
            kwargs["user"] = user
        return _method(url, *args, **kwargs)
