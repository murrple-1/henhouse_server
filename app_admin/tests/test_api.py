import asyncio
from typing import Any, Dict
from unittest.mock import Mock
import uuid

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

        if hasattr(request, "user") and not hasattr(request, "auser"):
            user = request.user

            async def auser():
                return user

            request.auser = auser

        return request


class ApiTestCase(TestCase):
    async def test_register(self):
        with self.settings(VALIDATE_EMAIL_DELIVERABILITY=False):
            test_client = TestAsyncClient(router)

            response = await test_client.post(
                "/register",
                json={
                    "username": "user1",
                    "email": "test@test.com",
                    "password": "aC0mplic?tedTestPassword",
                },
            )

            self.assertEqual(response.status_code, 204, response.content)

    async def test_register_alreadyexists(self):
        with self.settings(VALIDATE_EMAIL_DELIVERABILITY=False):
            test_client = TestAsyncClient(router)

            await User.objects.acreate_user("user1", "test@test.com", "Password1!")

            response = await test_client.post(
                "/register",
                json={
                    "username": "user1",
                    "email": "test@test.com",
                    "password": "aC0mplic?tedTestPassword",
                },
            )
            self.assertEqual(response.status_code, 409, response.content)

    async def test_register_weakpassword(self):
        with self.settings(VALIDATE_EMAIL_DELIVERABILITY=False):
            test_client = TestAsyncClient(router)

            response = await test_client.post(
                "/register",
                json={
                    "username": "user1",
                    "email": "test@test.com",
                    "password": "password",
                },
            )
            self.assertEqual(response.status_code, 422, response.content)

    async def test_register_bademail(self):
        with self.settings(VALIDATE_EMAIL_DELIVERABILITY=False):
            test_client = TestAsyncClient(router)

            response = await test_client.post(
                "/register",
                json={
                    "username": "user1",
                    "email": "notrealemail",
                    "password": "aC0mplic?tedTestPassword",
                },
            )
            self.assertEqual(response.status_code, 422, response.content)

    async def test_register_badusername(self):
        with self.settings(VALIDATE_EMAIL_DELIVERABILITY=False):
            test_client = TestAsyncClient(router)

            response = await test_client.post(
                "/register",
                json={
                    "username": "",
                    "email": "test@test.com",
                    "password": "aC0mplic?tedTestPassword",
                },
            )
            self.assertEqual(response.status_code, 422, response.content)

            response = await test_client.post(
                "/register",
                json={
                    "username": "user$",
                    "email": "test@test.com",
                    "password": "aC0mplic?tedTestPassword",
                },
            )
            self.assertEqual(response.status_code, 422, response.content)

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

    async def test_logout(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.post("/logout", user=user)
        self.assertEqual(response.status_code, 204, response.content)

    async def test_change_password(self):
        test_client = TestAsyncClient(router)

        user: User = await User.objects.acreate_user(
            "user1", "test@test.com", "password"
        )

        response = await test_client.put(
            "/user/password", json={"password": "aC0mplic?tedTestPassword"}, user=user
        )
        self.assertEqual(response.status_code, 204, response.content)

        self.assertTrue(await user.acheck_password("aC0mplic?tedTestPassword"))
        self.assertFalse(await user.acheck_password("password"))

    async def test_user_details(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", "password")

        response = await test_client.get("/user", user=user)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "uuid": str(user.uuid),
                "username": "user1",
                "email": "test@test.com",
                "attributes": {},
            },
        )

    async def test_user_lookup(self):
        test_client = TestAsyncClient(router)

        users = await asyncio.gather(
            User.objects.acreate_user("user1", "test1@test.com", "password"),
            User.objects.acreate_user("user2", "test2@test.com", "password"),
            User.objects.acreate_user("user3", "test3@test.com", "password"),
        )

        query_params = "&".join(f"userIds={u.uuid}" for u in users)

        response = await test_client.get(f"/user/lookup?{query_params}")
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, list)
        self.assertTrue(all(isinstance(e, dict) for e in json_))

        for user in users:
            self.assertIsNotNone(
                next(
                    (
                        e
                        for e in json_
                        if e
                        == {
                            "uuid": str(user.uuid),
                            "username": user.username,
                        }
                    ),
                    None,
                )
            )

    async def test_user_lookup_notfound(self):
        test_client = TestAsyncClient(router)

        query_params = "&".join([f"userIds={uuid.UUID(int=0)}"])

        response = await test_client.get(f"/user/lookup?{query_params}")
        self.assertEqual(response.status_code, 404, response.content)

    async def test_update_user_attributes(self):
        test_client = TestAsyncClient(router)

        user: User = await User.objects.acreate_user("user1", "test@test.com", None)

        self.assertEqual(user.attributes, {})

        response = await test_client.put(
            "/user/attributes",
            json={"attributes": {"test1": "value1", "test2": "value2"}},
            user=user,
        )
        self.assertEqual(response.status_code, 204, response.content)

        await user.arefresh_from_db()

        self.assertEqual(user.attributes, {"test1": "value1", "test2": "value2"})

        response = await test_client.put(
            "/user/attributes",
            json={"attributes": {"test1": None}},
            user=user,
        )
        self.assertEqual(response.status_code, 204, response.content)

        await user.arefresh_from_db()

        self.assertEqual(user.attributes, {"test2": "value2"})

    async def test_delete_user(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", "password")
        response = await test_client.delete(
            "/user",
            json={"password": "password"},
            user=user,
        )
        self.assertEqual(response.status_code, 204, response.content)

        with self.assertRaises(User.DoesNotExist):
            await User.objects.aget(uuid=user.uuid)

    async def test_delete_user_badpassword(self):
        test_client = TestAsyncClient(router)

        user1 = await User.objects.acreate_user("user1", "test1@test.com", None)
        response = await test_client.delete(
            "/user",
            json={"password": "password"},
            user=user1,
        )
        self.assertEqual(response.status_code, 401, response.content)

        user2 = await User.objects.acreate_user("user2", "test2@test.com", "password")
        response = await test_client.delete(
            "/user",
            json={"password": "badpassword"},
            user=user2,
        )
        self.assertEqual(response.status_code, 401, response.content)

    async def test_get_csrf_token(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/csrf")
        self.assertEqual(response.status_code, 204, response.content)
        self.assertIn("csrftoken", response._response.cookies)
