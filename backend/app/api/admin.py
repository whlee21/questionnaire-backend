import logging

from fastapi import APIRouter, Depends

from app.api.auth import get_current_admin
from app.models.admin import AdminUser
from app.schemas.admin import LogLevelIn, LogLevelOut

router = APIRouter()

_LEVEL_MAP: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


@router.get("/log-level", response_model=LogLevelOut)
async def get_log_level(
    admin: AdminUser = Depends(get_current_admin),
) -> LogLevelOut:
    level_name = logging.getLevelName(logging.root.level)
    return LogLevelOut(level=level_name)


@router.put("/log-level", response_model=LogLevelOut)
async def set_log_level(
    body: LogLevelIn,
    admin: AdminUser = Depends(get_current_admin),
) -> LogLevelOut:
    numeric_level = _LEVEL_MAP[body.level.value]
    logging.root.setLevel(numeric_level)
    for handler in logging.root.handlers:
        handler.setLevel(numeric_level)
    return LogLevelOut(level=body.level.value)
