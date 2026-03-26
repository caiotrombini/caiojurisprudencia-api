from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Optional

import httpx

from juris_api.core.config import Settings
from juris_api.core.constants import RETRYABLE_STATUSES
from juris_api.models.domain import ServicesContainer

logger = logging.getLogger('jurisprudencia_api.http')


def build_http_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout_seconds, connect=settings.http_connect_timeout_seconds),
        limits=httpx.Limits(
            max_connections=settings.http_max_connections,
            max_keepalive_connections=settings.http_max_keepalive_connections,
        ),
        headers={'User-Agent': settings.user_agent},
        follow_redirects=True,
    )


async def request_upstream(
    services: ServicesContainer,
    settings: Settings,
    method: str,
    url: str,
    *,
    provider: str,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
) -> Optional[httpx.Response]:
    async with services.upstream_semaphore:
        for attempt in range(1, settings.http_retries + 1):
            try:
                response = await services.http.request(method=method, url=url, params=params, json=json_body, headers=headers)
                if response.status_code in RETRYABLE_STATUSES:
                    if attempt == settings.http_retries:
                        logger.warning('[%s] upstream retornou %s em %s', provider, response.status_code, url)
                        return None
                    retry_after = response.headers.get('Retry-After')
                    await asyncio.sleep(min(int(retry_after), 5) if retry_after and retry_after.isdigit() else (0.35 * attempt) + random.uniform(0.0, 0.15))
                    continue
                response.raise_for_status()
                return response
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
                if attempt == settings.http_retries:
                    logger.warning('[%s] falha definitiva em %s: %s', provider, url, exc)
                    return None
                await asyncio.sleep((0.35 * attempt) + random.uniform(0.0, 0.15))
            except httpx.HTTPStatusError as exc:
                logger.warning('[%s] HTTP não-retentável %s em %s', provider, exc.response.status_code, url)
                return None
            except Exception as exc:
                logger.exception('[%s] erro inesperado em %s: %s', provider, url, exc)
                return None
    return None
