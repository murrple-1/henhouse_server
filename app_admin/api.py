import asyncio

from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError
from ninja import Query, Router
from django.http import Http404, HttpRequest, HttpResponse
from django.utils import timezone
from django.contrib.auth import (
    alogin as django_alogin,
    alogout as django_alogout,
    aauthenticate as django_aauthenticate,
)
from ninja.errors import HttpError
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from app_admin.models import User
from app_admin.security import must_auth
from app_admin.schemas import (
    LoginInSchema,
    RegisterInSchema,
    ChangePasswordInSchema,
    UserAttributesInSchema,
    UserDeleteInSchema,
    UserDetailsOutSchema,
    UserLookupInSchema,
    UserOutSchema,
)

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
    await django_alogout(request)
    return None


@router.put("/user/password", response={204: None}, auth=must_auth, tags=["auth"])
async def change_password(
    request: HttpRequest, input_change_password: ChangePasswordInSchema
):
    user = request.user
    assert isinstance(user, AbstractBaseUser)

    user.set_password(input_change_password.password)
    await user.asave(update_fields=("password",))

    return None


@router.post("/user/passwordreset", tags=["auth"])
async def request_password_reset(request: HttpRequest):
    # TODO implement
    return None


@router.post("/user/passwordresetconfirm", tags=["auth"])
async def password_reset_confirm(request: HttpRequest):
    # TODO implement
    return None


@router.get("/user", response=UserDetailsOutSchema, auth=must_auth, tags=["auth"])
async def user_details(request: HttpRequest):
    return request.user


@router.get("/user/lookup", response=list[UserOutSchema], tags=["auth"])
async def user_lookup(request: HttpRequest, lookup_input: Query[UserLookupInSchema]):
    user_ids_ = frozenset(lookup_input.user_ids)
    users = [u async for u in User.objects.filter(uuid__in=user_ids_)]

    if len(users) != len(user_ids_):
        raise Http404

    return users


@router.put("/user/attributes", response={204: None}, auth=must_auth, tags=["auth"])
async def update_user_attributes(
    request: HttpRequest, input_attributes: UserAttributesInSchema
):
    user = request.user
    assert isinstance(user, User)

    user.attributes.update(input_attributes.attributes)

    del_keys = set()
    for key, value in user.attributes.items():
        if value is None:
            del_keys.add(key)

    for key in del_keys:
        del user.attributes[key]

    await user.asave(update_fields=["attributes"])
    return None


@router.delete("/user", response={204: None}, auth=must_auth, tags=["auth"])
async def delete_user(request: HttpRequest, input_delete: UserDeleteInSchema):
    user = request.user
    assert isinstance(user, User)

    user_ = await django_aauthenticate(
        request, username=user.username, password=input_delete.password
    )
    if not user_:
        raise HttpError(401, "invalid credentials")

    await asyncio.gather(django_alogout(request), user.adelete())

    return None


@router.get("/csrf", tags=["auth"])
@ensure_csrf_cookie
@csrf_exempt
async def get_csrf_token(request: HttpRequest):
    return HttpResponse()
