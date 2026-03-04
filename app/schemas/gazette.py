from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  İstek Şemaları
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GazetteScrapeRequest(BaseModel):
    date: date


class GazetteCreate(BaseModel):
    date: date
    url: Optional[str] = None
    pdf_data: Optional[bytes] = None
    content: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Temel Gazette Response (eski — korunuyor)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GazetteResponse(BaseModel):
    id: int
    date: str
    url: Optional[str] = None
    has_pdf: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Frontend İçin Yeni Response Şemaları
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GazetteListItem(BaseModel):
    """
    /gazette/list endpoint'inden döner.
    Frontend kart listesi için gerekli minimum veri.

    Örnek JSON:
    {
        "id": 1,
        "date": "2026-03-03",
        "main_topic": "İstihdamı Koruma Destek Programı",
        "summary": "SGK kapsamında yeni destek...",
        "categories": ["Yönetmelik"],
        "importance_score": 8,
        "is_analyzed": true
    }
    """
    id: int
    date: str
    main_topic: Optional[str] = None
    summary: Optional[str] = None
    categories: list[str] = []
    tags: list[str] = []
    importance_score: Optional[int] = Field(None, ge=1, le=10)
    is_analyzed: bool = False
    created_at: datetime


class GazetteDetail(BaseModel):
    """
    /gazette/{id} endpoint'inden döner.
    Tek bir kaydın tüm detayları — frontend detay sayfası için.

    Örnek JSON:
    {
        "id": 1,
        "date": "2026-03-03",
        "url": "https://www.resmigazete.gov.tr/...",
        "summary": "SGK kapsamında yeni destek programı...",
        "main_topic": "İstihdamı Koruma Destek Programı",
        "related_topics": ["SGK", "İstihdam Teşviki"],
        "categories": ["Yönetmelik"],
        "tags": ["sgk", "istihdam", "destek"],
        "importance_score": 8,
        "is_analyzed": true,
        "created_at": "2026-03-03T01:05:00"
    }
    """
    id: int
    date: str
    url: Optional[str] = None
    summary: Optional[str] = None
    main_topic: Optional[str] = None
    related_topics: list[str] = []
    categories: list[str] = []
    tags: list[str] = []
    importance_score: Optional[int] = Field(None, ge=1, le=10)
    is_analyzed: bool = False
    created_at: datetime


class GazetteAnalyzeResponse(BaseModel):
    """
    /gazette/analyze/{id} endpoint'inden döner.
    Yeni yapılan analiz sonucu.

    Örnek JSON:
    {
        "gazette_id": 1,
        "summary": "SGK kapsamında yeni destek...",
        "main_topic": "İstihdamı Koruma Destek Programı",
        "related_topics": ["SGK", "İstihdam"],
        "categories": ["Yönetmelik"],
        "tags": ["sgk", "istihdam", "destek"],
        "importance_score": 8,
        "model": "gpt-4o-mini",
        "tokens_used": 847,
        "message": "Analiz başarıyla tamamlandı."
    }
    """
    gazette_id: int
    summary: str
    main_topic: str
    related_topics: list[str]
    categories: list[str]
    tags: list[str]
    importance_score: int = Field(ge=1, le=10)
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    message: str = "Analiz başarıyla tamamlandı."
