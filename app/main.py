"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import async_session_factory, init_db
from app.routers.patients import router as patients_router
from app.schemas.patient import ApiResponse
from app.seed import seed_demo_patient

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session_factory() as session:
        await seed_demo_patient(session)
    yield


app = FastAPI(
    title="Voice AI Patient Registration API",
    description="REST API for voice-based patient intake",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first.get("loc", []) if loc != "body")
    message = first.get("msg", "Validation error")
    if field:
        message = f"{field}: {message}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiResponse(
            data=None,
            error={"message": message, "code": "VALIDATION_ERROR"},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            data=None,
            error={"message": "Internal server error", "code": "INTERNAL_ERROR"},
        ).model_dump(),
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Voice AI Patient Registration API", "docs": "/docs", "dashboard": "/dashboard"}


static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/dashboard")
async def dashboard():
    dashboard_path = static_dir / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Dashboard not found"},
    )
