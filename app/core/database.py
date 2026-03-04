"""
app/core/database.py
─────────────────────
SQLAlchemy async motor ve session factory.

Neden async?
  Sync SQLAlchemy, FastAPI'nin async event-loop'unu bloklar.
  aiosqlite sürücüsü + AsyncSession sayesinde I/O bekleme süresinde
  başka request'ler işlenebilir → daha yüksek throughput.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# ── Async Motor ──────────────────────────────────────────────
# echo=True → geliştirmede SQL sorgularını terminale yazar
# check_same_thread=False → SQLite'ın thread kısıtını kaldırır
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

# ── Session Factory ──────────────────────────────────────────
# expire_on_commit=False → commit sonrası nesneyi tekrar yüklemez,
#   bu sayede async context dışında da attribute'lara erişilebilir.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ───────────────────────────────────────────────
# Tüm ORM modelleri bu sınıftan türeyecek
class Base(DeclarativeBase):
    pass


# ── Dependency ───────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI route'larında kullanılan veritabanı bağımlılığı.

    Kullanım:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...

    Her istek için yeni bir session açar, istek bitince kapatır.
    Hata olsa bile 'finally' bloğu session'ı kapatır.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()   # Hata yoksa değişiklikleri kaydet
        except Exception:
            await session.rollback() # Hata varsa geri al
            raise
        finally:
            await session.close()    # Her halükârda session'ı kapat
