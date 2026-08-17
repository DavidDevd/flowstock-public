from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from flowstock_api import __version__
from flowstock_api.api.errors import register_exception_handlers
from flowstock_api.api.router import api_router
from flowstock_api.config import Settings, get_settings
from flowstock_api.infrastructure.database import Database, DatabaseProbe
from flowstock_api.logging import configure_logging
from flowstock_api.middleware.correlation import CorrelationIdMiddleware
from flowstock_api.middleware.security_headers import SecurityHeadersMiddleware
from flowstock_api.observability import MetricsMiddleware, configure_tracing, metrics_response


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        yield
        application.state.database.close()

    app = FastAPI(
        title="FlowStock API",
        version=__version__,
        docs_url="/docs" if app_settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if app_settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.database = Database(app_settings.database_url)
    app.state.database_probe = DatabaseProbe(app.state.database.engine)

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=app_settings.allowed_host_list)
    if app_settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token", "X-Correlation-ID"],
        )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    app.add_api_route("/metrics", metrics_response, include_in_schema=False)
    configure_tracing(app, app_settings)
    return app


app = create_app()
