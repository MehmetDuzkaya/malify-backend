"""
app/models/__init__.py
──────────────────────
Tüm ORM modellerini buradan import ediyoruz.
Bu sayede alembic veya create_all() çağrısı,
tüm tabloları otomatik olarak tanır.
"""

from app.models.gazette import Gazette  # noqa: F401

__all__ = ["Gazette"]
