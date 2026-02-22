import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def auth_client(db, user):
    """DRF client pre-authenticated as `user`."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(db, admin_user):
    """DRF client pre-authenticated as an admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client
