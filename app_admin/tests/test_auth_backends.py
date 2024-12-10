from typing import ClassVar
from unittest.mock import Mock
import uuid

from django.http import HttpRequest
from django.test import TestCase

from app_admin.auth_backends import EmailBackend
from app_admin.models import User


class EmailBackendTestCase(TestCase):
    user_credentials = {"username": "test@test.com", "password": "test"}

    user: ClassVar[User]
    backend: ClassVar[EmailBackend]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.backend = EmailBackend()

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.user = User.objects.create_user("user1", "test@test.com", "test")

    def test_authenticate(self):
        self.assertEqual(
            EmailBackendTestCase.backend.authenticate(
                **EmailBackendTestCase.user_credentials,
                request=Mock(HttpRequest),
            ),
            EmailBackendTestCase.user,
        )

        self.assertIsNone(
            EmailBackendTestCase.backend.authenticate(
                request=Mock(HttpRequest),
                username="missing@test.com",
                password="test",
            )
        )

    def test_get_user(self):
        self.assertEqual(
            EmailBackendTestCase.backend.get_user(EmailBackendTestCase.user.pk),
            EmailBackendTestCase.user,
        )
        self.assertIsNone(EmailBackendTestCase.backend.get_user(uuid.UUID(int=0)))

        EmailBackendTestCase.user.is_active = False
        EmailBackendTestCase.user.save(update_fields=("is_active",))
        self.assertIsNone(
            EmailBackendTestCase.backend.get_user(EmailBackendTestCase.user.pk)
        )
