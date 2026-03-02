from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class GazetteScrapeRequest(BaseModel):
    date: date


class GazetteCreate(BaseModel):
    date: date
    url: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None


class GazetteResponse(BaseModel):
    id: int
    date: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
