from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        result = await self.db.execute(select(Analysis).where(Analysis.id == analysis_id))
        return result.scalar_one_or_none()

    async def get_by_gazette_id(self, gazette_id: int) -> list[Analysis]:
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.gazette_id == gazette_id)
            .order_by(Analysis.created_at.desc())
        )
        return result.scalars().all()

    async def create(self, gazette_id: int, result: dict) -> Analysis:
        analysis = Analysis(
            gazette_id=gazette_id,
            analysis_type=result["analysis_type"],
            result=result["result"],
            model=result.get("model"),
            tokens_used=result.get("tokens_used"),
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis

    async def delete(self, analysis_id: int) -> bool:
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            return False
        await self.db.delete(analysis)
        await self.db.commit()
        return True
