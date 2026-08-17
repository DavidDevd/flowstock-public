from fastapi import APIRouter

from flowstock_api.api.routes.health import router as health_router
from flowstock_api.api.routes.identity import router as identity_router
from flowstock_api.api.routes.master_data import router as master_data_router
from flowstock_api.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["platform"])
api_router.include_router(identity_router, prefix="/auth", tags=["identity"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(master_data_router, tags=["master-data"])
