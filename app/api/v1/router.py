from fastapi import APIRouter
from app.api.v1.routes import gazette, analysis, health

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(gazette.router, prefix="/gazettes", tags=["Gazettes"])
router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
