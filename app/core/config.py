"""
app/core/config.py
──────────────────
Pydantic-Settings ile .env dosyasını okur.
Tüm uygulama ayarları tek bir yerden yönetilir.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── Uygulama ─────────────────────────────────────────────
    app_name: str = "Malify Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Sunucu ───────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Veritabanı ───────────────────────────────────────────
    # aiosqlite: SQLite'ın async (non-blocking) sürücüsü
    database_url: str = "sqlite+aiosqlite:///./malify.db"

    # ── PDF Depolama ─────────────────────────────────────────
    # İndirilen PDF'lerin kaydedileceği klasör (proje kökünden göreli)
    pdf_storage_dir: str = "storage/pdfs"

    # ── OpenAI ───────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Resmî Gazete ─────────────────────────────────────────
    gazette_base_url: str = "https://www.resmigazete.gov.tr"

    # ── Zamanlama ────────────────────────────────────────────
    gazette_scrape_hour: int = 10
    gazette_scrape_minute: int = 0

    # .env dosyasını otomatik yükle; büyük/küçük harf duyarsız
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache  # Aynı nesneyi tekrar tekrar oluşturmamak için önbellek
def get_settings() -> Settings:
    """
    Uygulama boyunca tek bir Settings örneği döner.
    FastAPI Dependency Injection ile kullanım:
        def my_route(settings: Settings = Depends(get_settings)):
    """
    return Settings()
