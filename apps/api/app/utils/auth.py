from fastapi import Header, HTTPException
from app.core.config import settings


def require_ingest_api_key(x_api_key: str = Header(default="")) -> None:
    if x_api_key != settings.ingest_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def require_admin_api_key(x_admin_key: str = Header(default="")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
