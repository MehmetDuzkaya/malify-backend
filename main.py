"""
main.py
────────
FastAPI uygulamasının giriş noktası.

Sorumlulukları:
  1. FastAPI app örneği oluştur ve yapılandır
  2. CORS ayarla (frontend'in erişebilmesi için)
  3. Tüm route'ları kaydet
  4. Startup / shutdown lifecycle event'larını yönet
     - Veritabanı tablolarını oluştur
     - PDF depolama klasörünü hazırla
     - Günlük scrape scheduler'ı başlat / durdur
  5. Sağlık kontrolü endpoint'i sun (/health)

Çalıştırma:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine, Base
from app.services.scheduler import start_scheduler, stop_scheduler

# Tüm modeller import edilmeli ki Base.metadata onları tanısın
import app.models  # noqa: F401

settings = get_settings()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Lifecycle — Uygulama başlarken ve kapanırken çalışır
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    'yield' öncesi → startup (uygulama başlıyor)
    'yield' sonrası → shutdown (uygulama kapanıyor)

    asynccontextmanager kullanımı, ayrı on_event dekoratörlerine
    göre daha temiz ve test edilmesi daha kolaydır.
    """
    # ── STARTUP ──────────────────────────────────────────────
    print(f"🚀  {settings.app_name} v{settings.app_version} başlatılıyor...")

    # 1. Veritabanı tablolarını oluştur (yoksa)
    #    Üretimde bu işi Alembic yapar; geliştirme kolaylığı için burada bıraktık.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅  Veritabanı tabloları hazır.")

    # 2. PDF depolama klasörünü oluştur
    storage_path = Path(settings.pdf_storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)
    print(f"📁  PDF depolama klasörü: {storage_path.resolve()}")

    # 3. Günlük scrape scheduler'ı başlat
    start_scheduler()

    yield  # ← Uygulama burada çalışır

    # ── SHUTDOWN ─────────────────────────────────────────────
    stop_scheduler()
    await engine.dispose()  # Veritabanı bağlantı havuzunu kapat
    print("👋  Uygulama düzgün şekilde kapatıldı.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FastAPI Uygulaması
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Resmî Gazete PDF'lerini günlük çeken, AI ile analiz eden "
        "ve sonuçları veritabanına kaydeden backend API."
    ),
    # Swagger UI adresi: http://localhost:8000/docs
    docs_url="/docs",
    # ReDoc adresi: http://localhost:8000/redoc
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CORS (Cross-Origin Resource Sharing)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Frontend (Next.js vb.) farklı bir origin'den istek atabilmesi için gerekli.
# Üretimde allow_origins'i gerçek domain ile kısıtla!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://malify.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Route'ları Kaydet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tüm /api/v1/* endpoint'leri buradan eklenir
app.include_router(api_router)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Sağlık Kontrolü
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/health", tags=["System"])
async def health_check():
    """
    Uygulamanın ayakta olup olmadığını kontrol eder.
    Docker healthcheck, load balancer ve monitoring araçları kullanır.

    Örnek yanıt:
        {"status": "ok", "version": "0.1.0"}
    """
    return {"status": "ok", "version": settings.app_version}
