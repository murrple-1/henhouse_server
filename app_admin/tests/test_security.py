import datetime
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from app_admin.models import Token, User
from app_admin.security import (
    AHttpBasicAuth,
    AHttpBearer,
    TokenExpired,
    TokenInvalid,
    ASessionAuth,
)


class AHttpBasicAuthTestCase(TestCase):
    async def test_authenticate(self):
        user = await User.objects.acreate_user("user1", "test@test.com", "P4ssw0rd!")

        auth = AHttpBasicAuth()
        self.assertIsNone(
            await auth.authenticate(Mock(HttpRequest), "test@test.com", "bad_password")
        )

        user = await auth.authenticate(Mock(HttpRequest), "test@test.com", "P4ssw0rd!")
        self.assertIsInstance(user, User)
        assert isinstance(user, User)
        last_login = user.last_login
        assert isinstance(last_login, datetime.datetime)
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)


class AHttpBearerAuthTestCase(TestCase):
    async def test_authenticate(self):
        user = await User.objects.acreate_user("user1", "test@test.com", "P4ssw0rd!")
        token = await Token.objects.acreate(user=user)

        auth = AHttpBearer()
        with self.assertRaises(TokenInvalid):
            await auth.authenticate(Mock(HttpRequest), "bad_token")

        token_ = await auth.authenticate(Mock(HttpRequest), token.key)
        self.assertIsInstance(token_, Token)
        assert isinstance(token_, Token)
        last_login = token_.user.last_login
        assert isinstance(last_login, datetime.datetime), last_login
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)

    async def test_authenticate_with_expiry(self):
        user = await User.objects.acreate_user("user1", "test@test.com", "P4ssw0rd!")
        token = await Token.objects.acreate(
            user=user, expires_at=(timezone.now() + datetime.timedelta(minutes=5))
        )

        auth = AHttpBearer()
        token_ = await auth.authenticate(Mock(HttpRequest), token.key)
        self.assertIsInstance(token_, Token)
        assert isinstance(token_, Token)
        last_login = token_.user.last_login
        assert isinstance(last_login, datetime.datetime), last_login
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)

        token = await Token.objects.acreate(
            user=user, expires_at=(timezone.now() + datetime.timedelta(minutes=-5))
        )
        with self.assertRaises(TokenExpired):
            await auth.authenticate(Mock(HttpRequest), token.key)


class ASessionAuthTestCase(TestCase):
    async def test_authenticate(self):
        user = AnonymousUser()

        auth = ASessionAuth()

        request = Mock(HttpRequest)

        async def auser():
            return user

        request.auser = auser

        self.assertIsNone(await auth.authenticate(request, None))

        user = await User.objects.acreate_user("user1", "test@test.com", "P4ssw0rd!")

        self.assertIsNotNone(await auth.authenticate(request, None))
