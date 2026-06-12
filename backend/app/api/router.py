from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.devices import router as devices_router
from app.api.messages import router as messages_router
from app.api.topics import router as topics_router
from app.api.history import router as history_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(devices_router, prefix="/devices", tags=["devices"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
api_router.include_router(history_router, prefix="/messages/history", tags=["history"])
