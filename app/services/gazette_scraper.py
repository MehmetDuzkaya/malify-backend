"""
app/services/gazette_scraper.py
────────────────────────────────
Resmî Gazete PDF'ini web'den indirir ve local storage'a kaydeder.

Akış:
  1. Resmî Gazete sitesinden belirtilen tarihin PDF URL'ini çek
  2. PDF'i httpx ile async olarak indir
  3. storage/pdfs/<YYYY>/<MM>/<YYYY-MM-DD>.pdf yoluna kaydet
  4. Veritabanındaki Gazette kaydına pdf_path ve url'i yaz

TODO: Bu dosya iskelet halindedir. URL parsing mantığı
      Resmî Gazete'nin HTML yapısına göre tamamlanacak.
"""

import os
from datetime import date
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.gazette import Gazette

settings = get_settings()


async def scrape_and_save(target_date: date, db: AsyncSession) -> Gazette:
    """
    Verilen tarihe ait Resmî Gazete PDF'ini indirir ve kaydeder.

    Parametreler:
        target_date: İndirilecek gazetenin yayın tarihi
        db: Aktif veritabanı session'ı

    Dönüş:
        Güncellenmiş Gazette ORM nesnesi
    """
    date_str = target_date.strftime("%Y-%m-%d")

    # ── 1. Mevcut kaydı kontrol et ───────────────────────────
    result = await db.execute(select(Gazette).where(Gazette.date == date_str))
    gazette = result.scalar_one_or_none()
    if not gazette:
        gazette = Gazette(date=date_str)
        db.add(gazette)

    # ── 2. PDF URL'ini oluştur (TODO: gerçek URL pattern) ────
    # Resmî Gazete URL örneği: https://www.resmigazete.gov.tr/eskiler/2026/03/20260303.pdf
    year = target_date.strftime("%Y")
    month = target_date.strftime("%m")
    day = target_date.strftime("%d")
    pdf_url = f"{settings.gazette_base_url}/eskiler/{year}/{month}/{year}{month}{day}.pdf"
    gazette.url = pdf_url

    # ── 3. PDF'i async olarak indir ──────────────────────────
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(pdf_url)
        response.raise_for_status()  # HTTP hata varsa exception fırlat

    # ── 4. Kaydetme dizinini oluştur ─────────────────────────
    save_dir = Path(settings.pdf_storage_dir) / year / month
    save_dir.mkdir(parents=True, exist_ok=True)

    pdf_file_path = save_dir / f"{date_str}.pdf"
    pdf_file_path.write_bytes(response.content)

    gazette.pdf_path = str(pdf_file_path)

    await db.flush()   # ID'yi oluşturmak için flush (commit değil)
    return gazette
