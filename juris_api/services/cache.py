from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import BaseModel

from juris_api.models.domain import ServicesContainer


async def get_json_cache(services: ServicesContainer, key: str) -> Optional[dict[str, Any]]:
    cached = await services.redis.get(key)
    if not cached:
        return None
    try:
        return json.loads(cached)
    except json.JSONDecodeError:
        await services.redis.delete(key)
        return None


async def set_json_cache(services: ServicesContainer, key: str, payload: BaseModel | dict[str, Any], ttl_seconds: int) -> None:
    raw = payload.model_dump(mode='json') if isinstance(payload, BaseModel) else payload
    await services.redis.set(key, json.dumps(raw, ensure_ascii=False), ex=ttl_seconds)
