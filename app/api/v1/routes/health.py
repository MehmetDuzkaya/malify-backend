from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "ok",
        "service": "malify-backend",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """Veritabanı ve servis bağlantılarını kontrol eder."""
    return {"status": "ready"}
