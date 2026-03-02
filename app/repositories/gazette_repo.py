from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.gazette import Gazette
from app.schemas.gazette import GazetteCreate


class GazetteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Gazette]:
        result = await self.db.execute(
            select(Gazette).offset(skip).limit(limit).order_by(Gazette.date.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, gazette_id: int) -> Optional[Gazette]:
        result = await self.db.execute(select(Gazette).where(Gazette.id == gazette_id))
        return result.scalar_one_or_none()

    async def get_by_date(self, date_str: str) -> Optional[Gazette]:
        result = await self.db.execute(select(Gazette).where(Gazette.date == date_str))
        return result.scalar_one_or_none()

    async def create(self, data: GazetteCreate) -> Gazette:
        gazette = Gazette(
            date=str(data.date),
            url=data.url,
            file_path=data.file_path,
            content=data.content,
        )
        self.db.add(gazette)
        await self.db.commit()
        await self.db.refresh(gazette)
        return gazette

    async def delete(self, gazette_id: int) -> bool:
        gazette = await self.get_by_id(gazette_id)
        if not gazette:
            return False
        await self.db.delete(gazette)
        await self.db.commit()
        return True
