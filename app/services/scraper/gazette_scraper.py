import httpx
from bs4 import BeautifulSoup
from datetime import date
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ScrapingException
from app.services.storage.file_manager import FileManager


class GazetteScraper:
    """Resmî Gazete web sitesinden metin çeken servis."""

    def __init__(self):
        self.base_url = settings.SCRAPE_BASE_URL
        self.delay = settings.SCRAPE_DELAY_SECONDS
        self.file_manager = FileManager()

    async def scrape_by_date(self, target_date: date) -> dict:
        """
        Verilen tarihe ait Resmî Gazete sayfasını çeker,
        metin olarak ayrıştırır ve .txt olarak kaydeder.
        """
        url = self._build_url(target_date)
        logger.info(f"Scraping başlatıldı: {url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ScrapingException(f"HTTP hatası: {e}") from e

        content = self._parse_content(response.text)
        file_path = await self.file_manager.save_gazette(target_date, content)

        logger.info(f"Scraping tamamlandı. Dosya: {file_path}")
        return {
            "date": target_date,
            "url": url,
            "file_path": str(file_path),
            "content": content,
        }

    def _build_url(self, target_date: date) -> str:
        formatted = target_date.strftime("%Y%m%d")
        return f"{self.base_url}/eskiler/{target_date.year}/{formatted}.htm"

    def _parse_content(self, html: str) -> str:
        from app.services.scraper.parser import GazetteParser
        return GazetteParser.extract_text(html)
