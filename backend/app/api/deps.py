from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.services.data_backend_service import DataBackendService
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_data_backend_service(db=Depends(get_db)) -> DataBackendService:
    return DataBackendService(db=db)


def get_current_user(service: DataBackendService = Depends(get_data_backend_service), token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc
    user = service.get_user_by_username(username)
    if not user or not user.get("active", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")
    return user
