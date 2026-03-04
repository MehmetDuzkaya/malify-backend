"""
app/models/gazette.py
──────────────────────
SQLAlchemy ORM modeli — veritabanı tablosunu temsil eder.

Her alan için tip, nullable ve açıklama bilgisi verilmiştir.
JSON alanları (categories, tags, related_topics) SQLite'ta TEXT
olarak saklanır; okuma/yazma sırasında otomatik dönüşüm yapılır.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text, Float, DateTime, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Gazette(Base):
    """
    `gazettes` tablosu.

    Kolon açıklamaları:
    ┌─────────────────┬──────────┬─────────────────────────────────────────┐
    │ Kolon           │ Tip      │ Açıklama                                │
    ├─────────────────┼──────────┼─────────────────────────────────────────┤
    │ id              │ INTEGER  │ Otomatik artan birincil anahtar          │
    │ date            │ TEXT     │ Yayın tarihi — "YYYY-MM-DD" formatında  │
    │ url             │ TEXT     │ Resmî Gazete'deki kaynak URL             │
    │ pdf_path        │ TEXT     │ Local disk'teki PDF dosyasının yolu      │
    │ summary         │ TEXT     │ AI tarafından üretilen özet              │
    │ main_topic      │ TEXT     │ Ana konu başlığı                         │
    │ related_topics  │ TEXT     │ JSON dizisi: ilgili alt konular          │
    │ categories      │ TEXT     │ JSON dizisi: kategori etiketleri         │
    │ tags            │ TEXT     │ JSON dizisi: arama etiketleri            │
    │ importance_score│ REAL     │ 1–10 arası önem puanı (AI tarafından)   │
    │ is_analyzed     │ INTEGER  │ Analiz edildi mi? (0/1 boolean)          │
    │ created_at      │ DATETIME │ Kaydın oluşturulma zamanı (UTC)          │
    │ analyzed_at     │ DATETIME │ Analizin tamamlandığı zaman (UTC)        │
    └─────────────────┴──────────┴─────────────────────────────────────────┘
    """

    __tablename__ = "gazettes"

    # ── Kimlik & Zaman Damgaları ─────────────────────────────
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Birincil anahtar",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        # default: insert sırasında Python tarafında UTC şimdi ata
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Kaydın oluşturulma zamanı (UTC)",
    )

    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="AI analizinin tamamlandığı zaman (UTC)",
    )

    # ── Gazete Verisi ────────────────────────────────────────
    date: Mapped[str] = mapped_column(
        String(10),           # "YYYY-MM-DD" → 10 karakter yeterli
        nullable=False,
        index=True,           # Tarihe göre sorgular için index
        unique=True,          # Aynı tarihte iki kayıt olmasın
        comment="Yayın tarihi (YYYY-MM-DD)",
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Resmî Gazete kaynak URL",
    )

    pdf_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Local disk'teki PDF dosyasının yolu",
    )

    # ── AI Analiz Sonuçları ──────────────────────────────────
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI tarafından üretilen özet metin",
    )

    main_topic: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Ana konu başlığı",
    )

    # JSON olarak saklanan listeler — okuma/yazma için yardımcı property'ler
    _related_topics: Mapped[Optional[str]] = mapped_column(
        "related_topics", Text, nullable=True, default="[]"
    )

    _categories: Mapped[Optional[str]] = mapped_column(
        "categories", Text, nullable=True, default="[]"
    )

    _tags: Mapped[Optional[str]] = mapped_column(
        "tags", Text, nullable=True, default="[]"
    )

    importance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="1–10 önem puanı",
    )

    is_analyzed: Mapped[bool] = mapped_column(
        Integer,              # SQLite'ta bool → 0/1 integer
        default=0,
        nullable=False,
        comment="Analiz tamamlandı mı?",
    )

    # ── JSON Yardımcı Property'leri ──────────────────────────
    # SQLite TEXT'te saklanan JSON'ı Python list olarak sun.

    @property
    def related_topics(self) -> list[str]:
        if not self._related_topics:
            return []
        return json.loads(self._related_topics)

    @related_topics.setter
    def related_topics(self, value: list[str]) -> None:
        self._related_topics = json.dumps(value, ensure_ascii=False)

    @property
    def categories(self) -> list[str]:
        if not self._categories:
            return []
        return json.loads(self._categories)

    @categories.setter
    def categories(self, value: list[str]) -> None:
        self._categories = json.dumps(value, ensure_ascii=False)

    @property
    def tags(self) -> list[str]:
        if not self._tags:
            return []
        return json.loads(self._tags)

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = json.dumps(value, ensure_ascii=False)

    # ── Debug Yardımcısı ─────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Gazette id={self.id} date={self.date!r} "
            f"analyzed={bool(self.is_analyzed)}>"
        )
