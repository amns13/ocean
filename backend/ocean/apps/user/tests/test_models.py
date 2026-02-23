from django.test import TestCase

from ocean.apps.user.tests.factories import UserFactory


class TestUserModel(TestCase):
    def test_user_str(self):
        """Test that str returns user's username"""
        user = UserFactory()
        self.assertEqual(str(user), user.username)
