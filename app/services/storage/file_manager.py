import aiofiles
from pathlib import Path
from datetime import date
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import StorageException


class FileManager:
    """Gazete metinlerini .txt olarak dosya sistemine kaydeden/okuyan servis."""

    def __init__(self):
        self.base_dir: Path = settings.DATA_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, target_date: date) -> Path:
        date_dir = self.base_dir / target_date.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir / "gazette.txt"

    async def save_gazette(self, target_date: date, content: str) -> Path:
        """Metni belirtilen tarihe ait klasöre kaydeder."""
        file_path = self._get_file_path(target_date)
        try:
            async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
                await f.write(content)
            logger.info(f"Dosya kaydedildi: {file_path}")
            return file_path
        except OSError as e:
            raise StorageException(f"Dosya kaydedilemedi: {e}") from e

    async def read_gazette(self, target_date: date) -> str:
        """Belirtilen tarihe ait .txt dosyasını okur."""
        file_path = self._get_file_path(target_date)
        if not file_path.exists():
            raise StorageException(f"Dosya bulunamadı: {file_path}")
        try:
            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                return await f.read()
        except OSError as e:
            raise StorageException(f"Dosya okunamadı: {e}") from e

    async def delete_gazette(self, target_date: date) -> bool:
        """Belirtilen tarihe ait dosyayı siler."""
        file_path = self._get_file_path(target_date)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Dosya silindi: {file_path}")
            return True
        return False

    def list_all(self) -> list[Path]:
        """Tüm kayıtlı .txt dosyalarının yollarını döner."""
        return sorted(self.base_dir.rglob("*.txt"))
