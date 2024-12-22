from django.db import IntegrityError
from ninja import Router
from django.http import HttpRequest
from django.utils import timezone
from django.contrib.auth import (
    alogin as django_alogin,
    alogout as django_alogout,
    aauthenticate as django_aauthenticate,
)
from ninja.errors import HttpError

from app_admin.models import User
from app_admin.security import must_auth
from app_admin.schemas import LoginInSchema, RegisterInSchema

router = Router()


@router.post("/register", response={204: None}, tags=["auth"])
async def register(request: HttpRequest, input_register: RegisterInSchema):
    try:
        await User.objects.acreate_user(
            input_register.username, input_register.email, input_register.password
        )
        # TODO send validation email, etc.
    except IntegrityError:
        raise HttpError(409, "user already exists")

    return None


@router.post("/login", response={204: None}, tags=["auth"])
async def login(request: HttpRequest, input_login: LoginInSchema):
    user = await django_aauthenticate(
        request, username=input_login.username_email, password=input_login.password
    )
    if not user:
        user = await django_aauthenticate(
            request, email=input_login.username_email, password=input_login.password
        )

    if not user:
        raise HttpError(401, "invalid credentials")

    await django_alogin(request, user)

    if not input_login.stay_logged_in:
        request.session.set_expiry(0)

    user.last_login = timezone.now()
    await user.asave(update_fields=("last_login",))

    return None


@router.post("/logout", response={204: None}, auth=must_auth, tags=["auth"])
async def logout(request: HttpRequest):
    # TODO implement
    await django_alogout(request)
    return None


@router.put("/user/password", auth=must_auth, tags=["auth"])
async def change_password(request: HttpRequest):
    # TODO implement
    return None


@router.post("/user/passwordreset", tags=["auth"])
async def request_password_reset(request: HttpRequest):
    # TODO implement
    return None


@router.post("/user/passwordresetconfirm", tags=["auth"])
async def password_reset_confirm(request: HttpRequest):
    # TODO implement
    return None


@router.get("/user", auth=must_auth, tags=["auth"])
async def user_details(request: HttpRequest):
    # TODO implement
    return None


@router.put("/user/attributes", auth=must_auth, tags=["auth"])
async def update_user_attributes(request: HttpRequest):
    # TODO implement
    return None


@router.delete("/user", auth=must_auth, tags=["auth"])
async def delete_user(request: HttpRequest):
    # TODO implement
    return None
