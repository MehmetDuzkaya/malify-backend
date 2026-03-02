from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db_session
from app.schemas.analysis import AnalysisResponse, AnalysisRequest
from app.repositories.analysis_repo import AnalysisRepository
from app.services.ai.analyzer import AIAnalyzer
from app.core.exceptions import AnalysisNotFoundException, GazetteNotFoundException
from app.repositories.gazette_repo import GazetteRepository

router = APIRouter()


@router.post("/{gazette_id}", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_gazette(
    gazette_id: int,
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Belirtilen gazeteyi AI ile analiz eder."""
    gazette_repo = GazetteRepository(db)
    gazette = await gazette_repo.get_by_id(gazette_id)
    if not gazette:
        raise GazetteNotFoundException(gazette_id)

    analyzer = AIAnalyzer()
    result = await analyzer.analyze(gazette.content, analysis_type=request.analysis_type)

    analysis_repo = AnalysisRepository(db)
    saved = await analysis_repo.create(gazette_id=gazette_id, result=result)
    return saved


@router.get("/{gazette_id}", response_model=List[AnalysisResponse])
async def get_analyses_for_gazette(
    gazette_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Bir gazeteye ait tüm analiz sonuçlarını döner."""
    repo = AnalysisRepository(db)
    return await repo.get_by_gazette_id(gazette_id)


@router.get("/result/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Belirli bir analiz sonucunu döner."""
    repo = AnalysisRepository(db)
    analysis = await repo.get_by_id(analysis_id)
    if not analysis:
        raise AnalysisNotFoundException(analysis_id)
    return analysis
