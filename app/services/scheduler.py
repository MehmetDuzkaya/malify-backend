"""
app/services/scheduler.py
──────────────────────────
APScheduler ile günlük otomatik gazete çekme işini yönetir.

Ayarlar .env üzerinden okunur:
  GAZETTE_SCRAPE_HOUR=6
  GAZETTE_SCRAPE_MINUTE=0

Bu sayede her sabah 06:00 UTC'de Resmî Gazete otomatik çekilir.
"""

from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.services.gazette_scraper import scrape_and_save

settings = get_settings()

# Uygulama boyunca tek bir scheduler örneği
scheduler = AsyncIOScheduler(timezone="UTC")


async def _daily_scrape_job() -> None:
    """
    Scheduler tarafından günlük çalıştırılan iş.
    Bugünün gazetesini indirir ve veritabanına kaydeder.
    """
    today = date.today()
    async with AsyncSessionLocal() as db:
        try:
            gazette = await scrape_and_save(today, db)
            await db.commit()
            print(f"[Scheduler] {today} gazetesi kaydedildi → id={gazette.id}")
        except Exception as exc:
            await db.rollback()
            print(f"[Scheduler] HATA ({today}): {exc}")


def start_scheduler() -> None:
    """
    Uygulamanın startup event'ında çağrılır.
    Her gün belirtilen saat ve dakikada çalışacak job'ı ekler.
    """
    scheduler.add_job(
        _daily_scrape_job,
        trigger=CronTrigger(
            hour=settings.gazette_scrape_hour,
            minute=settings.gazette_scrape_minute,
        ),
        id="daily_gazette_scrape",
        replace_existing=True,       # Uygulama yeniden başlatılırsa çakışmasın
    )
    scheduler.start()
    print(
        f"[Scheduler] Başlatıldı — her gün "
        f"{settings.gazette_scrape_hour:02d}:{settings.gazette_scrape_minute:02d} UTC"
    )


def stop_scheduler() -> None:
    """
    Uygulamanın shutdown event'ında çağrılır.
    Açık kalan job'ları temiz bir şekilde kapatır.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] Durduruldu.")
