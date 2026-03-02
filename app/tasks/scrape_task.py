from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.logging import logger

scheduler = AsyncIOScheduler()


async def scheduled_scrape():
    """Her gün gece yarısı bugünün gazetesini çeker."""
    from datetime import date
    from app.services.scraper.gazette_scraper import GazetteScraper
    from app.db.session import AsyncSessionLocal
    from app.repositories.gazette_repo import GazetteRepository
    from app.schemas.gazette import GazetteCreate

    logger.info("Zamanlanmış scraping başladı.")
    scraper = GazetteScraper()
    today = date.today()

    try:
        result = await scraper.scrape_by_date(today)
        async with AsyncSessionLocal() as db:
            repo = GazetteRepository(db)
            await repo.create(GazetteCreate(**result))
        logger.info(f"Zamanlanmış scraping tamamlandı: {today}")
    except Exception as e:
        logger.error(f"Zamanlanmış scraping hatası: {e}")
