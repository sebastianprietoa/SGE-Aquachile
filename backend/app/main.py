from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.areas import router as areas_router
from app.api.routes.auth import router as auth_router
from app.api.routes.energy_uses import router as energy_uses_router
from app.api.routes.energy_management import router as energy_management_router
from app.api.routes.measurements import router as measurements_router
from app.api.routes.systems import router as systems_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import *  # noqa: F403
from app.services.seed_service import seed_database
from app.services.seed_service_v2 import seed_database_v2
from app.utils.seed_csv import seed_csv

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0", description="Módulo de gestión de información energética basado en ISO 50001 y Decreto 28.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(systems_router)
app.include_router(areas_router)
app.include_router(energy_uses_router)
app.include_router(energy_management_router)
app.include_router(measurements_router)
app.include_router(alerts_router)


@app.on_event("startup")
def on_startup() -> None:
    if settings.data_backend.lower() == "postgres":
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database(db)
            seed_database_v2(db)
        finally:
            db.close()
    else:
        seed_csv(reset=False)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
