"""
app/services/ai_analyzer.py
────────────────────────────
PDF dosyasını OpenAI'ya yükler ve analiz sonuçlarını döner.

Akış:
  1. pdf_path'teki PDF'i oku
  2. PyMuPDF (fitz) ile metni çıkar
  3. OpenAI Chat API'ye metin + prompt gönder
  4. Yanıtı parse et (özet, konu, kategori, skor)
  5. Gazette kaydını güncelle

TODO: Bu dosya iskelet halindedir.
      OpenAI API çağrısı gerçek API key ile tamamlanacak.
"""

from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.gazette import Gazette

settings = get_settings()

# OpenAI async client (uygulama boyunca tek örnek)
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

# Analiz için sistem talimatı
SYSTEM_PROMPT = """
Sen Türkiye Resmî Gazetesi analist asistanısın.
Sana verilen Resmî Gazete metnini analiz et ve şu bilgileri JSON formatında döndür:

{
  "summary": "200-300 kelimelik Türkçe özet",
  "main_topic": "Ana konu başlığı (tek cümle)",
  "related_topics": ["konu1", "konu2", "konu3"],
  "categories": ["Yönetmelik|Kanun|Karar|Tebliğ|İlan"],
  "tags": ["arama_etiketi1", "arama_etiketi2"],
  "importance_score": 7
}

importance_score: 1 (rutin) – 10 (kritik ulusal öneme sahip) arasında tam sayı.
"""


async def analyze_gazette(gazette: Gazette, db: AsyncSession) -> Gazette:
    """
    Verilen Gazette nesnesinin PDF'ini okuyup AI ile analiz eder.

    Parametreler:
        gazette: pdf_path dolu Gazette ORM nesnesi
        db: Aktif veritabanı session'ı

    Dönüş:
        Analiz sonuçlarıyla güncellenmiş Gazette nesnesi
    """
    if not gazette.pdf_path or not Path(gazette.pdf_path).exists():
        raise FileNotFoundError(f"PDF bulunamadı: {gazette.pdf_path}")

    # ── 1. PDF'den metin çıkar ────────────────────────────────
    pdf_text = _extract_text_from_pdf(gazette.pdf_path)

    # Çok uzun metinleri kes (token limiti aşımını önle)
    pdf_text = pdf_text[:12_000]

    # ── 2. OpenAI API çağrısı ─────────────────────────────────
    response = await openai_client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Aşağıdaki Resmî Gazete metnini analiz et:\n\n{pdf_text}"},
        ],
    )

    # ── 3. Yanıtı parse et ────────────────────────────────────
    import json
    result = json.loads(response.choices[0].message.content)

    # ── 4. Gazette kaydını güncelle ───────────────────────────
    gazette.summary = result.get("summary", "")
    gazette.main_topic = result.get("main_topic", "")
    gazette.related_topics = result.get("related_topics", [])
    gazette.categories = result.get("categories", [])
    gazette.tags = result.get("tags", [])
    gazette.importance_score = float(result.get("importance_score", 5))
    gazette.is_analyzed = True
    gazette.analyzed_at = datetime.now(timezone.utc)

    await db.flush()
    return gazette


def _extract_text_from_pdf(pdf_path: str) -> str:
    """
    PyMuPDF (fitz) kullanarak PDF'den düz metin çıkarır.
    Her sayfanın metni birleştirilir.
    """
    text_parts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)
