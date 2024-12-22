from typing import Annotated

from ninja import Field, Schema
from pydantic import AfterValidator
from email_validator import validate_email, EmailNotValidError


def _validate_email_with_dns(value: str) -> str:
    try:
        emailinfo = validate_email(value, check_deliverability=False)
        return emailinfo.normalized
    except EmailNotValidError as e:
        raise ValueError(e) from e


class RegisterInSchema(Schema):
    username: str
    email: Annotated[str, AfterValidator(_validate_email_with_dns)]
    password: str


class LoginInSchema(Schema):
    username_email: str = Field(alias="usernameEmail")
    password: str
    stay_logged_in: bool = Field(alias="stayLoggedIn")
