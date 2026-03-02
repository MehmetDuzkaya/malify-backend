from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import AIServiceException
from app.services.ai.prompts import ANALYSIS_PROMPTS


class AIAnalyzer:
    """OpenAI kullanarak gazete metinlerini analiz eden servis."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def analyze(self, content: str, analysis_type: str = "summary") -> dict:
        """
        Verilen metni belirtilen analiz türüne göre işler.

        analysis_type seçenekleri:
        - summary: Kısa özet
        - keywords: Anahtar kelimeler
        - classification: Konu sınıflandırması
        - full: Tüm analizler
        """
        prompt = ANALYSIS_PROMPTS.get(analysis_type)
        if not prompt:
            raise AIServiceException(f"Geçersiz analiz türü: {analysis_type}")

        logger.info(f"AI analizi başlatıldı: type={analysis_type}, length={len(content)}")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": f"{prompt['user_prefix']}\n\n{content[:8000]}"},
                ],
                temperature=0.3,
            )
        except Exception as e:
            raise AIServiceException(f"OpenAI hatası: {e}") from e

        result_text = response.choices[0].message.content
        logger.info("AI analizi tamamlandı.")
        return {
            "analysis_type": analysis_type,
            "result": result_text,
            "model": self.model,
            "tokens_used": response.usage.total_tokens,
        }
