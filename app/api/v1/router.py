"""
app/api/v1/router.py
─────────────────────
v1 API'sindeki tüm route'ları tek bir router'a toplar.
Yeni bir endpoint grubu eklendiğinde sadece buraya eklenir.
"""

from fastapi import APIRouter
from app.api.v1.routes import gazette

api_router = APIRouter(prefix="/api/v1")

# Gazette route'larını ekle
api_router.include_router(gazette.router)
