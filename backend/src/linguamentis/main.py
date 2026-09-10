"""LinguaMentis FastAPI Application.

Per Architecture.md: Main application entry point providing CORS, structlog,
domain exception handling, database initialization, and routing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from linguamentis.api.router import api_router
from linguamentis.infrastructure.configuration import get_settings
from linguamentis.infrastructure.database.models import Base
from linguamentis.infrastructure.database.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from linguamentis.infrastructure.database.session import get_engine, get_session_factory
from linguamentis.shared.exceptions import (
    AIGatewayError,
    DomainError,
    InvalidStateTransitionError,
    LinguaMentisError,
    NotFoundError,
)
from linguamentis.shared.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Process lifecycle: initialize database tables & default user on startup."""
    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        await user_repo.ensure_default_user(
            default_id=settings.default_user_id, display_name="Default Learner"
        )
        await session.commit()

    logger.info("app.started", env=settings.app_env)
    yield
    logger.info("app.shutting_down")


app = FastAPI(
    title="LinguaMentis API",
    description="Gamified AI debate platform for B2/C1 German learners (Six Thinking Hats).",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "env": settings.app_env}


# Exception handlers
@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": str(exc)},
    )


@app.exception_handler(InvalidStateTransitionError)
async def handle_invalid_transition(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid State Transition",
            "message": str(exc),
            "current_state": exc.current_state,
            "attempted_event": exc.attempted_event,
        },
    )


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Domain Violation", "message": str(exc)},
    )


@app.exception_handler(AIGatewayError)
async def handle_ai_error(request: Request, exc: AIGatewayError) -> JSONResponse:
    logger.error("api.ai_gateway_error", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": "AI Gateway Failure", "message": str(exc)},
    )


@app.exception_handler(LinguaMentisError)
async def handle_generic_application_error(
    request: Request, exc: LinguaMentisError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Application Error", "message": str(exc)},
    )
