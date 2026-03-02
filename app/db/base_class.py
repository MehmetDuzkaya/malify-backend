# Tüm modelleri buraya import et — Alembic migration'ların modelleri görmesi için gerekli
from app.db.base import Base  # noqa
from app.models.gazette import Gazette  # noqa
from app.models.analysis import Analysis  # noqa
