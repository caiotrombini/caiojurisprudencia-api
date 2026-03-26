from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal, Optional

import httpx
import redis.asyncio as redis

from juris_api.models.schemas import ResultadoJuridico


@dataclass(slots=True)
class ProviderExecution:
    tribunal: str
    provider: str
    results: list[ResultadoJuridico]
    latency_ms: int
    status: Literal['ok', 'vazio', 'erro', 'degradado']
    message: Optional[str] = None


@dataclass(slots=True)
class ServicesContainer:
    redis: redis.Redis
    http: httpx.AsyncClient
    upstream_semaphore: asyncio.Semaphore
    started_at: float
