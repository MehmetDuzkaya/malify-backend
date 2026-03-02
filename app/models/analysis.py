from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    gazette_id = Column(Integer, ForeignKey("gazettes.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String(50), nullable=False)   # summary, keywords, classification, full
    result = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gazette = relationship("Gazette", backref="analyses")
