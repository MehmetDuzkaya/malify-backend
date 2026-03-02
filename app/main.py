from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import MalifyBaseException
from app.api.v1.router import router as api_v1_router
from app.db.session import engine
from app.db.base_class import Base
from app.tasks.scrape_task import scheduler, scheduled_scrape


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlangıcı
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} başlatılıyor...")

    # Veritabanı tablolarını oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Veritabanı tabloları hazır.")

    # Zamanlanmış görevleri başlat
    scheduler.add_job(scheduled_scrape, "cron", hour=0, minute=5, id="daily_scrape")
    scheduler.start()
    logger.info("✅ Zamanlanmış görevler başlatıldı.")

    yield

    # Uygulama kapanışı
    scheduler.shutdown()
    await engine.dispose()
    logger.info("🛑 Uygulama kapatıldı.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global hata yakalayıcı
    @app.exception_handler(MalifyBaseException)
    async def malify_exception_handler(request: Request, exc: MalifyBaseException):
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message},
        )

    # API rotalarını bağla
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
