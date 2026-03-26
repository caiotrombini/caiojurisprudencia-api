from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from juris_api.api.routes.health import router as health_router
from juris_api.api.routes.meta import router as meta_router
from juris_api.api.routes.search import router as search_router
from juris_api.clients.http import build_http_client
from juris_api.core.config import get_settings
from juris_api.core.logging import setup_logging
from juris_api.models.domain import ServicesContainer

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    http_client = build_http_client(settings)
    redis_client = redis.from_url(settings.redis_url, encoding='utf-8', decode_responses=True)
    await redis_client.ping()
    app.state.services = ServicesContainer(
        redis=redis_client,
        http=http_client,
        upstream_semaphore=asyncio.Semaphore(settings.max_upstream_concurrency),
        started_at=time.time(),
    )
    try:
        yield
    finally:
        await http_client.aclose()
        await redis_client.aclose()


app = FastAPI(
    title='Search Jurisprudence API',
    version='4.0.0',
    description='API de busca jurisprudencial com prioridade para fontes oficiais, caching em Redis, rate limit distribuído e resposta jurídica normalizada.',
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(health_router)
app.include_router(meta_router)
app.include_router(search_router)
