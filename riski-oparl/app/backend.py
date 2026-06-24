"""FastAPI application factory for the OParl publishing service."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.db import get_engine, init_engine
from app.routers.oparl import router as oparl_router
from app.seed import ensure_system_and_body
from app.settings import get_settings

logger = logging.getLogger(__name__)

API_DESCRIPTION = """
This service publishes the RISKI database according to the
[OParl 1.1 specification](https://oparl.org).

### How to use it
OParl is **link-driven** — start at the entry point and follow the URLs:

1. `GET /oparl/v1/system` — the entry point. Its `body` field links to the body list.
2. `GET /oparl/v1/bodies` — pick a body; its `organization` / `person` / `meeting` /
   `paper` fields are URLs to paginated **external lists**.
3. Follow object URLs (e.g. a paper's `originatorPerson`) to fetch individual objects.

Every object's `id` is the canonical URL on this API; the original RIS web page is
provided in the `web` field.

### External lists
Support pagination via `page` and time filtering via `created_since`, `created_until`,
`modified_since`, `modified_until`. Responses contain `data`, `pagination` and `links`
(`first` / `prev` / `next` / `last`).
"""

OPENAPI_TAGS = [
    {"name": "system", "description": "Service health and the OParl entry point."},
    {"name": "OParl: System", "description": "The OParl System object — the API entry point."},
    {"name": "OParl: Body", "description": "Bodies (Körperschaften) and their scoped external lists."},
    {"name": "OParl: Lists", "description": "Paginated, time-filterable external lists of objects."},
    {"name": "OParl: Objects", "description": "Individual OParl objects retrieved by id."},
]


def create_app() -> FastAPI:
    settings = get_settings()
    init_engine(settings.core.db.database_url.encoded_string())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Ensure the OParl entry-point objects exist. Failures (e.g. DB down at
        # startup) are logged but do not prevent the service from starting.
        try:
            with Session(get_engine()) as session:
                ensure_system_and_body(session, settings)
        except Exception:
            logger.exception("Could not seed OParl System/Body on startup")
        yield

    docs_enabled = settings.enable_docs
    app = FastAPI(
        title="RISKI OParl API",
        version="0.1.0",
        summary="OParl 1.1 publishing API for Munich's political information system (RIS).",
        description=API_DESCRIPTION,
        contact={"name": "Landeshauptstadt München", "url": "https://github.com/it-at-m/riski"},
        license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )

    # OParl clients/crawlers fetch cross-origin; the data is public and read-only.
    # CORSMiddleware handles preflight when an Origin header is present.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    # OParl 1.1 requires Access-Control-Allow-Origin: * on *every* JSON response,
    # including non-browser requests that send no Origin header.
    @app.middleware("http")
    async def add_cors_header(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        return response

    @app.get("/healthz", tags=["system"], summary="Liveness check")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    if docs_enabled:

        @app.get("/", include_in_schema=False)
        def root():
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/docs")

    app.include_router(oparl_router)
    return app


backend = create_app()
