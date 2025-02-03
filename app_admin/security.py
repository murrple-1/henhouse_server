import datetime
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import aauthenticate
from django.contrib.auth.models import AnonymousUser
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils import timezone
from ninja.security import HttpBasicAuth as _HttpBasicAuth
from ninja.security import HttpBearer as _HttpBearer
from ninja.security.session import SessionAuth as _SessionAuth

from app_admin.models import Token

_TOKEN_EXPIRY_INTERVAL: datetime.timedelta


@receiver(setting_changed)
def _load_global_settings(*args: Any, **kwargs: Any):
    global _TOKEN_EXPIRY_INTERVAL

    _TOKEN_EXPIRY_INTERVAL = settings.TOKEN_EXPIRY_INTERVAL


_load_global_settings()


async def anonymous_fallback(request: HttpRequest):
    user = AnonymousUser()
    request.user = user

    async def auser():
        return user

    request.auser = auser

    return user


class AHttpBasicAuth(_HttpBasicAuth):
    async def authenticate(
        self, request: HttpRequest, username: str, password: str
    ) -> Optional[Any]:
        user = await aauthenticate(request, username=username, password=password)
        if user:
            user.last_login = timezone.now()
            await user.asave(update_fields=("last_login",))
            request.user = user

            async def auser():
                return user

            request.auser = auser
        return user


class TokenInvalid(Exception):
    pass


class TokenExpired(Exception):
    pass


class AHttpBearer(_HttpBearer):
    async def authenticate(self, request: HttpRequest, token: str) -> Optional[Any]:
        token_obj: Token
        try:
            token_obj = await Token.objects.select_related("user").aget(key=token)
        except Token.DoesNotExist:
            raise TokenInvalid

        if token_obj.expires_at is not None:
            now = timezone.now()
            if token_obj.expires_at <= now:
                await token_obj.adelete()
                raise TokenExpired

            token_obj.expires_at = now + _TOKEN_EXPIRY_INTERVAL
            await token_obj.asave(update_fields=("expires_at",))

        user = token_obj.user
        user.last_login = timezone.now()
        await user.asave(update_fields=("last_login",))
        request.user = user

        async def auser():
            return user

        request.auser = auser

        return token_obj


class ASessionAuth(_SessionAuth):
    async def authenticate(
        self, request: HttpRequest, key: Optional[str]
    ) -> Optional[Any]:
        user = await request.auser()
        if user.is_authenticated:
            return user

        return None


must_auth = [ASessionAuth(), AHttpBasicAuth(), AHttpBearer()]
auth_optional = must_auth + [anonymous_fallback]
