from typing import Annotated, Any
import re

from django.core.exceptions import ValidationError
from ninja import Field, Schema, ModelSchema
from pydantic import AfterValidator
from email_validator import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.conf import settings

from app_admin.models import User

_VALIDATE_EMAIL_DELIVERABILITY: bool


@receiver(setting_changed)
def _load_global_settings(*args: Any, **kwargs: Any):
    global _VALIDATE_EMAIL_DELIVERABILITY

    _VALIDATE_EMAIL_DELIVERABILITY = settings.VALIDATE_EMAIL_DELIVERABILITY


_load_global_settings()


def _validate_username(value: str) -> str:
    if len(value) < 1:
        raise ValueError("must not be empty")

    if not re.search(r"^[A-Z0-9_]+$", value, re.IGNORECASE):
        raise ValueError("must contain only letters, numbers, and underscores")

    return value


def _validate_email(value: str) -> str:
    emailinfo = validate_email(
        value, check_deliverability=_VALIDATE_EMAIL_DELIVERABILITY
    )
    return emailinfo.normalized


def _validate_password_strength(value: str) -> str:
    try:
        validate_password(value)
        return value
    except ValidationError as e:
        raise ValueError("\n".join(e.messages))


class RegisterInSchema(Schema):
    username: Annotated[str, AfterValidator(_validate_username)]
    email: Annotated[str, AfterValidator(_validate_email)]
    password: Annotated[str, AfterValidator(_validate_password_strength)]


class LoginInSchema(Schema):
    username_email: str = Field(alias="usernameEmail")
    password: str
    stay_logged_in: bool = Field(alias="stayLoggedIn")


class ChangePasswordInSchema(Schema):
    password: Annotated[str, AfterValidator(_validate_password_strength)]


class UserOutSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["uuid", "username"]


class UserDetailsOutSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["uuid", "username", "email", "attributes"]


class UserAttributesInSchema(Schema):
    attributes: dict[str, str | None]


class UserDeleteInSchema(Schema):
    password: str


class UserLookupInSchema(Schema):
    user_ids: list[str] = Field(default_factory=list, alias="userIds")
