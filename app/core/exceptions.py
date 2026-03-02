from fastapi import HTTPException, status


class MalifyBaseException(Exception):
    """Tüm uygulama hatalarının temel sınıfı."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ScrapingException(MalifyBaseException):
    """Web scraping sırasında oluşan hatalar."""
    pass


class StorageException(MalifyBaseException):
    """Dosya sistemi işlemlerinde oluşan hatalar."""
    pass


class AIServiceException(MalifyBaseException):
    """AI servisinde oluşan hatalar."""
    pass


class GazetteNotFoundException(HTTPException):
    def __init__(self, gazette_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gazete bulunamadı: id={gazette_id}",
        )


class AnalysisNotFoundException(HTTPException):
    def __init__(self, analysis_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analiz bulunamadı: id={analysis_id}",
        )
