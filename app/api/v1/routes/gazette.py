"""
app/api/v1/routes/gazette.py
─────────────────────────────
Resmî Gazete ile ilgili tüm HTTP endpoint'leri.

Endpoint'ler:
  GET  /gazette/list                → Tüm gazeteleri listele
  GET  /gazette/{id}                → Tek gazete detayı
  POST /gazette/scrape              → PDF indir & kaydet
  POST /gazette/analyze/{id}        → AI ile analiz et
  POST /gazette/scrape-and-analyze  → İndir + Analiz (tek tuş)
  POST /gazette/today               → Bugünü çek + analiz et (kısayol)
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.gazette import Gazette
from app.schemas.gazette import (
    GazetteScrapeRequest,
    GazetteListItem,
    GazetteDetail,
    GazetteAnalyzeResponse,
)
from app.services.gazette_scraper import scrape_and_save
from app.services.ai_analyzer import analyze_gazette as run_ai_analysis

router = APIRouter(prefix="/gazette", tags=["Gazette"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GET /gazette/list — Tüm gazeteleri listele
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.get("/list", response_model=list[GazetteListItem])
async def list_gazettes(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Veritabanındaki tüm gazete kayıtlarını sayfalanmış döner."""
    result = await db.execute(
        select(Gazette).order_by(Gazette.date.desc()).offset(skip).limit(limit)
    )
    gazettes = result.scalars().all()

    return [
        GazetteListItem(
            id=g.id,
            date=g.date,
            main_topic=g.main_topic,
            summary=g.summary,
            categories=g.categories,
            tags=g.tags,
            importance_score=g.importance_score,
            is_analyzed=bool(g.is_analyzed),
            created_at=g.created_at,
        )
        for g in gazettes
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GET /gazette/{gazette_id} — Tek gazete detayı
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.get("/{gazette_id}", response_model=GazetteDetail)
async def get_gazette(gazette_id: int, db: AsyncSession = Depends(get_db)):
    """Tek bir gazetenin tüm detaylarını döner."""
    gazette = await db.get(Gazette, gazette_id)
    if not gazette:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gazette id={gazette_id} bulunamadı.",
        )

    return GazetteDetail(
        id=gazette.id,
        date=gazette.date,
        url=gazette.url,
        summary=gazette.summary,
        main_topic=gazette.main_topic,
        related_topics=gazette.related_topics,
        categories=gazette.categories,
        tags=gazette.tags,
        importance_score=gazette.importance_score,
        is_analyzed=bool(gazette.is_analyzed),
        created_at=gazette.created_at,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POST /gazette/scrape — Sadece PDF indir ve kaydet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/scrape", status_code=status.HTTP_201_CREATED)
async def scrape_gazette(
    payload: GazetteScrapeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Belirtilen tarihe ait Resmî Gazete PDF'ini indirir ve veritabanına kaydeder.
    Body:  {"date": "2026-03-04"}
    """
    existing = await db.execute(
        select(Gazette).where(Gazette.date == str(payload.date))
    )
    found = existing.scalar_one_or_none()
    if found and found.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{payload.date} tarihli gazete zaten indirilmiş (id={found.id}).",
        )

    try:
        gazette = await scrape_and_save(payload.date, db)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PDF indirilemedi: {exc}",
        )

    return {
        "message": f"{payload.date} tarihli gazete başarıyla indirildi.",
        "gazette_id": gazette.id,
        "pdf_path": gazette.pdf_path,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POST /gazette/analyze/{gazette_id} — AI ile analiz et
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/analyze/{gazette_id}", response_model=GazetteAnalyzeResponse)
async def analyze_gazette_endpoint(
    gazette_id: int,
    db: AsyncSession = Depends(get_db),
):
    """PDF önceden indirilmiş olmalıdır (/scrape ile)."""
    gazette = await db.get(Gazette, gazette_id)
    if not gazette:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gazette id={gazette_id} bulunamadı.",
        )

    if not gazette.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PDF henüz indirilmemiş. Önce /scrape endpoint'ini çağırın.",
        )

    try:
        gazette = await run_ai_analysis(gazette, db)
        await db.commit()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analiz hatası: {exc}",
        )

    return GazetteAnalyzeResponse(
        gazette_id=gazette.id,
        summary=gazette.summary,
        main_topic=gazette.main_topic,
        related_topics=gazette.related_topics,
        categories=gazette.categories,
        tags=gazette.tags,
        importance_score=gazette.importance_score,
        message="Analiz başarıyla tamamlandı.",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POST /gazette/scrape-and-analyze — TEK TUŞLA HER ŞEYİ YAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/scrape-and-analyze", response_model=GazetteAnalyzeResponse)
async def scrape_and_analyze(
    payload: GazetteScrapeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Tek bir istekle:
      1. PDF'i indir
      2. AI ile analiz et
      3. Sonuçları veritabanına kaydet

    Body:  {"date": "2026-03-04"}
    """
    # Zaten analiz edilmişse tekrar yapma
    existing = await db.execute(
        select(Gazette).where(Gazette.date == str(payload.date))
    )
    found = existing.scalar_one_or_none()
    if found and found.is_analyzed:
        return GazetteAnalyzeResponse(
            gazette_id=found.id,
            summary=found.summary or "",
            main_topic=found.main_topic or "",
            related_topics=found.related_topics,
            categories=found.categories,
            tags=found.tags,
            importance_score=found.importance_score or 5,
            message="Bu tarih zaten analiz edilmiş, mevcut sonuç döndürülüyor.",
        )

    # 1. PDF İndir
    try:
        gazette = await scrape_and_save(payload.date, db)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PDF indirilemedi: {exc}",
        )

    # 2. AI Analiz
    try:
        gazette = await run_ai_analysis(gazette, db)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analiz hatası: {exc}",
        )

    return GazetteAnalyzeResponse(
        gazette_id=gazette.id,
        summary=gazette.summary,
        main_topic=gazette.main_topic,
        related_topics=gazette.related_topics,
        categories=gazette.categories,
        tags=gazette.tags,
        importance_score=gazette.importance_score,
        message="Gazete indirildi ve analiz tamamlandı ✅",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POST /gazette/today — BUGÜNÜ ÇEK + ANALİZ ET (kısayol)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@router.post("/today", response_model=GazetteAnalyzeResponse)
async def scrape_today(db: AsyncSession = Depends(get_db)):
    """
    Bugünün gazetesini indirir ve AI ile analiz eder.
    Hiçbir parametre gerekmez — tarihi otomatik alır.
    """
    today = date.today()
    payload = GazetteScrapeRequest(date=today)
    return await scrape_and_analyze(payload, db)
