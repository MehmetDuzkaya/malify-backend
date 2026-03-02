from app.core.logging import logger


async def analyze_pending_gazettes():
    """Henüz analiz edilmemiş gazete kayıtlarını işler."""
    from app.db.session import AsyncSessionLocal
    from app.repositories.gazette_repo import GazetteRepository
    from app.repositories.analysis_repo import AnalysisRepository
    from app.services.ai.analyzer import AIAnalyzer

    logger.info("Bekleyen gazete analizleri başlatıldı.")
    analyzer = AIAnalyzer()

    async with AsyncSessionLocal() as db:
        gazette_repo = GazetteRepository(db)
        analysis_repo = AnalysisRepository(db)

        gazettes = await gazette_repo.get_all(limit=10)
        for gazette in gazettes:
            existing = await analysis_repo.get_by_gazette_id(gazette.id)
            if existing:
                continue
            if not gazette.content:
                continue
            try:
                result = await analyzer.analyze(gazette.content, analysis_type="summary")
                await analysis_repo.create(gazette_id=gazette.id, result=result)
                logger.info(f"Gazete analiz edildi: id={gazette.id}")
            except Exception as e:
                logger.error(f"Analiz hatası (id={gazette.id}): {e}")
