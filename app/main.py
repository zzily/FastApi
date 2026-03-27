from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import add_middlewares


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.app_title)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=list(settings.cors_allow_methods),
        allow_headers=list(settings.cors_allow_headers),
    )
    add_middlewares(app)
    add_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
