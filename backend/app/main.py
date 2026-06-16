import logging
import re

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

_SENSITIVE_FIELDS = {"JWT_SECRET", "ADMIN_PASSWORD", "DATABASE_URL"}


def _mask(field: str, value: object) -> str:
    raw = str(value)
    if field in _SENSITIVE_FIELDS and raw:
        visible = min(4, len(raw))
        return raw[:visible] + "****"
    return raw


class _FcmTokenScrubFilter(logging.Filter):
    _PATTERN = re.compile(r'[A-Za-z0-9_\-:]{100,}')

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._PATTERN.sub('[FCM_TOKEN_REDACTED]', record.msg)
        if record.args:
            record.args = tuple(
                self._PATTERN.sub('[FCM_TOKEN_REDACTED]', str(a)) if isinstance(a, str) else a
                for a in (record.args if isinstance(record.args, tuple) else (record.args,))
            )
        return True


def create_app() -> FastAPI:
    settings = get_settings()

    log_level = getattr(logging, settings.LOG_LEVEL)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    logging.root.setLevel(log_level)
    scrub_filter = _FcmTokenScrubFilter()
    for handler in logging.root.handlers:
        handler.addFilter(scrub_filter)

    for field, value in settings.model_dump().items():
        logger.debug("config %s = %s", field, _mask(field, value))

    app = FastAPI(
        title="PushNotify API",
        version="0.1.0",
        description="Firebase push notification sender console API",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.get("/health", tags=["system"])
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")

    return app
