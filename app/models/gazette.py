from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.base import Base


class Gazette(Base):
    __tablename__ = "gazettes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    url = Column(String(512), nullable=True)
    file_path = Column(String(512), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
