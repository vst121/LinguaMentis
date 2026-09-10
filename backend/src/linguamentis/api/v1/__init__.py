"""API V1 package."""

from fastapi import APIRouter

from linguamentis.api.v1.learning import router as learning_router
from linguamentis.api.v1.mindquests import router as mindquests_router

v1_router = APIRouter()
v1_router.include_router(mindquests_router)
v1_router.include_router(learning_router)
