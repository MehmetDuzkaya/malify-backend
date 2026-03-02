from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class AnalysisType(str, Enum):
    summary = "summary"
    keywords = "keywords"
    classification = "classification"
    full = "full"


class AnalysisRequest(BaseModel):
    analysis_type: AnalysisType = AnalysisType.summary


class AnalysisResponse(BaseModel):
    id: int
    gazette_id: int
    analysis_type: str
    result: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
