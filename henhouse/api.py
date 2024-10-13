from ninja import NinjaAPI
from ninja.security import django_auth

from art.api import router as art_router

api = NinjaAPI(auth=django_auth)

api.add_router("/art/", art_router)
