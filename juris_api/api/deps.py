from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from juris_api.core.config import Settings, get_settings
from juris_api.models.domain import ServicesContainer

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


def get_services(request: Request) -> ServicesContainer:
    return request.app.state.services


def get_app_settings() -> Settings:
    return get_settings()


def require_api_key(api_key: Optional[str] = Depends(api_key_header), settings: Settings = Depends(get_app_settings)) -> str:
    if not api_key or api_key not in settings.api_keys_set:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='API key inválida ou ausente. Use o header X-API-Key.')
    return api_key
