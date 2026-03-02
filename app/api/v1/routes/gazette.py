from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db_session
from app.schemas.gazette import GazetteCreate, GazetteResponse, GazetteScrapeRequest
from app.repositories.gazette_repo import GazetteRepository
from app.services.scraper.gazette_scraper import GazetteScraper
from app.core.exceptions import GazetteNotFoundException

router = APIRouter()


@router.get("/", response_model=List[GazetteResponse])
async def list_gazettes(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
):
    """Tüm gazete kayıtlarını sayfalı olarak döner."""
    repo = GazetteRepository(db)
    return await repo.get_all(skip=skip, limit=limit)


@router.get("/{gazette_id}", response_model=GazetteResponse)
async def get_gazette(
    gazette_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Belirli bir gazete kaydını döner."""
    repo = GazetteRepository(db)
    gazette = await repo.get_by_id(gazette_id)
    if not gazette:
        raise GazetteNotFoundException(gazette_id)
    return gazette


@router.post("/scrape", status_code=status.HTTP_202_ACCEPTED)
async def scrape_gazette(
    request: GazetteScrapeRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Belirtilen tarihe ait Resmî Gazete'yi scrape eder ve kaydeder."""
    scraper = GazetteScraper()
    result = await scraper.scrape_by_date(request.date)
    repo = GazetteRepository(db)
    saved = await repo.create(GazetteCreate(**result))
    return {"message": "Scraping tamamlandı", "gazette_id": saved.id}


@router.delete("/{gazette_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gazette(
    gazette_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Gazete kaydını siler."""
    repo = GazetteRepository(db)
    deleted = await repo.delete(gazette_id)
    if not deleted:
        raise GazetteNotFoundException(gazette_id)
