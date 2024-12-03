import datetime
from unittest.mock import Mock

from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from app_admin.models import Token, User
from app_admin.security import HttpBasicAuth, HttpBearer, TokenExpired, TokenInvalid


class HttpBasicAuthTestCase(TestCase):
    def test_authenticate(self):
        user = User.objects.create_user("test@test.com", "P4ssw0rd!")

        auth = HttpBasicAuth()
        self.assertIsNone(
            auth.authenticate(Mock(HttpRequest), "test@test.com", "bad_password")
        )

        user = auth.authenticate(Mock(HttpRequest), "test@test.com", "P4ssw0rd!")
        self.assertIsInstance(user, User)
        assert isinstance(user, User)
        last_login = user.last_login
        assert isinstance(last_login, datetime.datetime)
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)


class HttpBearerAuthTestCase(TestCase):
    def test_authenticate(self):
        user = User.objects.create_user("test@test.com", "P4ssw0rd!")
        token = Token.objects.create(user=user)

        auth = HttpBearer()
        with self.assertRaises(TokenInvalid):
            auth.authenticate(Mock(HttpRequest), "bad_token")

        token_ = auth.authenticate(Mock(HttpRequest), token.key)
        self.assertIsInstance(token_, Token)
        assert isinstance(token_, Token)
        last_login = token_.user.last_login
        assert isinstance(last_login, datetime.datetime), last_login
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)

    def test_authenticate_with_expiry(self):
        user = User.objects.create_user("test@test.com", "P4ssw0rd!")
        token = Token.objects.create(
            user=user, expires_at=(timezone.now() + datetime.timedelta(minutes=5))
        )

        auth = HttpBearer()
        token_ = auth.authenticate(Mock(HttpRequest), token.key)
        self.assertIsInstance(token_, Token)
        assert isinstance(token_, Token)
        last_login = token_.user.last_login
        assert isinstance(last_login, datetime.datetime), last_login
        self.assertLessEqual(abs((timezone.now() - last_login).total_seconds()), 5.0)

        token = Token.objects.create(
            user=user, expires_at=(timezone.now() + datetime.timedelta(minutes=-5))
        )
        with self.assertRaises(TokenExpired):
            auth.authenticate(Mock(HttpRequest), token.key)
