import os
import shutil
from pathlib import Path
from typing import Optional
from app.config import settings

class StorageService:
    """
    Storage abstraction layer for survey imagery, vectors, masks, and generated reports.
    Designed for local disk storage with seamless AWS S3 interchangeability.
    """
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or settings.STORAGE_PATH

    def get_survey_dir(self, survey_id: int) -> Path:
        p = self.base_path / f"survey_{survey_id:04d}"
        for sub in ["input", "processed", "masks", "vectors", "reports"]:
            os.makedirs(p / sub, exist_ok=True)
        return p

    def save_upload_file(self, survey_id: int, file_obj, filename: str, subfolder: str = "input") -> Path:
        survey_dir = self.get_survey_dir(survey_id)
        target_path = survey_dir / subfolder / filename
        with open(target_path, "wb") as f:
            shutil.copyfileobj(file_obj, f)
        return target_path

    def get_file_path(self, survey_id: int, filename: str, subfolder: str = "input") -> Optional[Path]:
        path = self.get_survey_dir(survey_id) / subfolder / filename
        if path.exists():
            return path
        return None

storage_service = StorageService()
