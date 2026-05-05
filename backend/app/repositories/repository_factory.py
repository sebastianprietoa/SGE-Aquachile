from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.csv_repository import CSVRepository


@dataclass(slots=True)
class PostgresRepository:
    db: Session


class RepositoryFactory:
    @staticmethod
    def create(db: Session | None = None) -> Any:
        settings = get_settings()
        if settings.data_backend.lower() == "csv":
            csv_dir = Path(__file__).resolve().parents[2] / "data" / "csv"
            return CSVRepository(csv_dir)
        if db is None:
            raise ValueError("Se requiere una sesión de base de datos para DATA_BACKEND=postgres")
        return PostgresRepository(db=db)

