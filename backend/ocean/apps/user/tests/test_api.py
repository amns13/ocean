import json
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from faker import Faker

from ocean.apps.user.tests.factories import UserFactory

faker = Faker()


class TestLoginUserApi(TestCase):
    login_url = reverse("api-1:login")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.password = faker.password()
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.user.refresh_from_db()

    def call_login_api(self, data):
        return self.client.post(self.login_url, data=json.dumps(data), content_type="application/json")

    def test_login_fails_for_wrong_password(self):
        while (wrong_password := faker.password()) == self.password:
            continue
        response = self.call_login_api({"username": self.user.username, "password": wrong_password})
        self.assertEqual(401, response.status_code)
        self.assertDictEqual({"detail": "Invalid username or password."}, response.json())

    def test_login_succesful_for_valid_credentials(self):
        response = self.call_login_api({"username": self.user.username, "password": self.password})
        self.assertDictEqual(
            {"uid": str(self.user.uid), "email": self.user.email, "username": self.user.username}, response.json()
        )

    def test_login_fails_if_username_not_provided(self):
        response = self.call_login_api({"password": self.password})
        self.assertEqual(422, response.status_code, response.json())

    def test_login_fails_if_password_not_provided(self):
        response = self.call_login_api({"username": self.user.username})
        self.assertEqual(422, response.status_code, response.json())

    @mock.patch("ocean.apps.user.api.authenticate")
    def test_login_returns_details_if_user_already_authenticated(self, mock_authenticate):
        self.client.force_login(self.user)
        response = self.call_login_api({"username": self.user.username, "password": self.password})
        mock_authenticate.assert_not_called()
        self.assertDictEqual(
            {"uid": str(self.user.uid), "email": self.user.email, "username": self.user.username}, response.json()
        )
