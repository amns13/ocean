import pytest

from ocean.apps.user.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_user_str(self):
        """Test that str returns user's username"""
        user = UserFactory()
        assert str(user) == user.username
