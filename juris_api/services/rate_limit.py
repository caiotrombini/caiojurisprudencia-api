from __future__ import annotations

import time

from fastapi import HTTPException, status

from juris_api.core.config import Settings
from juris_api.models.domain import ServicesContainer
from juris_api.utils.text import sha256_hexdigest

RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


async def enforce_rate_limit(services: ServicesContainer, settings: Settings, api_key: str) -> None:
    now_bucket = int(time.time() // settings.rate_limit_window_seconds)
    redis_key = f"rl:{sha256_hexdigest(api_key)}:{now_bucket}"
    current, ttl = await services.redis.eval(RATE_LIMIT_LUA, 1, redis_key, settings.rate_limit_window_seconds)
    if int(current) > settings.rate_limit_max:
        retry_after = max(int(ttl), 1)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'message': 'Rate limit excedido.',
                'max_por_janela': settings.rate_limit_max,
                'janela_segundos': settings.rate_limit_window_seconds,
                'retry_after_seconds': retry_after,
            },
            headers={'Retry-After': str(retry_after)},
        )
