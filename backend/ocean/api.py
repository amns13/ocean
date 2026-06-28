from ninja import NinjaAPI

from ocean.apps.page.api import router as page_router
from ocean.apps.user.api import router as user_router
from ocean.utils.renderers import CustomJsonRender

api = NinjaAPI(renderer=CustomJsonRender(), urls_namespace="api-1")

api.add_router("", page_router)
api.add_router("/auth/", user_router)
