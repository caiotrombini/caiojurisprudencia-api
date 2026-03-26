import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
from dataclasses import dataclass

import httpx
import pytest
from fastapi import Request

from juris_api.api.deps import get_services
from juris_api.main import app


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.counters = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value

    async def delete(self, key):
        self.store.pop(key, None)

    async def ping(self):
        return True

    async def aclose(self):
        return None

    async def eval(self, script, numkeys, key, ttl):
        self.counters[key] = self.counters.get(key, 0) + 1
        return [self.counters[key], ttl]


@dataclass
class FakeServices:
    redis: FakeRedis
    http: httpx.AsyncClient
    upstream_semaphore: asyncio.Semaphore
    started_at: float = 0.0


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    fake_services = FakeServices(redis=FakeRedis(), http=httpx.AsyncClient(transport=transport, base_url='http://testserver'), upstream_semaphore=asyncio.Semaphore(3))
    app.dependency_overrides[get_services] = lambda request=None: fake_services
    async with httpx.AsyncClient(transport=transport, base_url='http://testserver') as client:
        yield client
    app.dependency_overrides.clear()
