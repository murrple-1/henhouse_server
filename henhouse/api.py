from django.http import HttpRequest
from ninja import NinjaAPI

from app_admin.security import TokenExpired, TokenInvalid
from art.api import router as art_router

api = NinjaAPI(csrf=True)


@api.exception_handler(TokenInvalid)
def on_token_invalid(request: HttpRequest, exc: Exception):
    return api.create_response(request, {"detail": "Token invalid"}, status=401)


@api.exception_handler(TokenExpired)
def on_token_expired(request: HttpRequest, exc: Exception):
    return api.create_response(request, {"detail": "Token expired"}, status=401)


api.add_router("/art/", art_router)
