"""Root API Router."""

from fastapi import APIRouter

from linguamentis.api.v1 import v1_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(v1_router)
