from ninja import NinjaAPI
from art.api import router as art_router

api = NinjaAPI()

api.add_router("/art/", art_router)
