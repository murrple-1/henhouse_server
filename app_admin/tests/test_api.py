from typing import Any, Dict
from unittest.mock import Mock

from django.test import TestCase
from ninja.testing import TestAsyncClient as TestAsyncClient_
from django.contrib.sessions.backends.cache import SessionStore

from app_admin.models import User
from app_admin.api import router


class TestAsyncClient(TestAsyncClient_):
    def _build_request(
        self, method: str, path: str, data: Dict, request_params: Any
    ) -> Mock:
        request = super()._build_request(method, path, data, request_params)
        request.session = SessionStore()
        return request


class ApiTestCase(TestCase):
    async def test_register(self):
        test_client = TestAsyncClient(router)

        response = await test_client.post(
            "/register",
            json={
                "username": "user1",
                "email": "test@test.com",
                "password": "Password1!",
            },
        )

        self.assertEqual(response.status_code, 204, response.content)

    async def test_register_alreadyexists(self):
        test_client = TestAsyncClient(router)

        await User.objects.acreate_user("user1", "test@test.com", "Password1!")

        response = await test_client.post(
            "/register",
            json={
                "username": "user1",
                "email": "test@test.com",
                "password": "Password1!",
            },
        )
        self.assertEqual(response.status_code, 409, response.content)

    async def test_login(self):
        test_client = TestAsyncClient(router)

        await User.objects.acreate_user("user1", "test@test.com", "Password1!")

        response = await test_client.post(
            "/login",
            json={
                "usernameEmail": "user1",
                "password": "Password1!",
                "stayLoggedIn": False,
            },
        )
        self.assertEqual(response.status_code, 204, response.content)

        response = await test_client.post(
            "/login",
            json={
                "usernameEmail": "test@test.com",
                "password": "Password1!",
                "stayLoggedIn": False,
            },
        )
        self.assertEqual(response.status_code, 204, response.content)

        response = await test_client.post(
            "/login",
            json={
                "usernameEmail": "user1",
                "password": "badpassword",
                "stayLoggedIn": False,
            },
        )
        self.assertEqual(response.status_code, 401, response.content)
