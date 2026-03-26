from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from juris_api.api.deps import get_app_settings, get_services
from juris_api.core.constants import SUPPORTED_TRIBUNAIS
from juris_api.core.config import Settings
from juris_api.models.domain import ServicesContainer
from juris_api.models.schemas import HealthResponse

router = APIRouter(tags=['Utilitários'])


@router.get('/health', response_model=HealthResponse, summary='Saúde da API')
async def health(services: ServicesContainer = Depends(get_services), settings: Settings = Depends(get_app_settings)):
    redis_status = 'ok'
    status_value = 'ok'
    try:
        await services.redis.ping()
    except Exception:
        redis_status = 'erro'
        status_value = 'degradado'
    return HealthResponse(
        status=status_value,
        versao='4.1.0',
        redis=redis_status,
        uptime_segundos=round(time.time() - services.started_at, 2),
        tribunais_suportados=len(SUPPORTED_TRIBUNAIS),
        cache_ttl_seconds=settings.cache_ttl_seconds,
        rate_limit_max=settings.rate_limit_max,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
    )
