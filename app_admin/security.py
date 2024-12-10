import datetime
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils import timezone
from ninja.security import HttpBasicAuth as _HttpBasicAuth
from ninja.security import HttpBearer as _HttpBearer
from ninja.security import django_auth

from app_admin.models import Token

_TOKEN_EXPIRY_INTERVAL: datetime.timedelta


@receiver(setting_changed)
def _load_global_settings(*args: Any, **kwargs: Any):
    global _TOKEN_EXPIRY_INTERVAL

    _TOKEN_EXPIRY_INTERVAL = settings.TOKEN_EXPIRY_INTERVAL


_load_global_settings()


def anonymous_fallback(request: HttpRequest):
    user = AnonymousUser()
    request.user = user
    return user


class HttpBasicAuth(_HttpBasicAuth):
    def authenticate(
        self, request: HttpRequest, username: str, password: str
    ) -> Optional[Any]:
        user = authenticate(request, username=username, password=password)
        if user:
            user.last_login = timezone.now()
            user.save(update_fields=("last_login",))
            request.user = user
        return user


class TokenInvalid(Exception):
    pass


class TokenExpired(Exception):
    pass


class HttpBearer(_HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        token_obj: Token
        try:
            token_obj = Token.objects.get(key=token)
        except Token.DoesNotExist:
            raise TokenInvalid

        if token_obj.expires_at is not None:
            now = timezone.now()
            if token_obj.expires_at <= now:
                token_obj.delete()
                raise TokenExpired

            token_obj.expires_at = now + _TOKEN_EXPIRY_INTERVAL
            token_obj.save(update_fields=("expires_at",))

        user = token_obj.user
        user.last_login = timezone.now()
        user.save(update_fields=("last_login",))
        request.user = user
        return token_obj


must_auth = [django_auth, HttpBasicAuth(), HttpBearer()]
auth_optional = must_auth + [anonymous_fallback]
