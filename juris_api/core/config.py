from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    api_keys: list[str] = Field(default_factory=lambda: ['dev-key-123'], alias='API_KEYS')
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')
    datajud_token: str = Field(default='', alias='DATAJUD_TOKEN')
    datajud_base_url: str = Field(default='https://api-publica.datajud.cnj.jus.br', alias='DATAJUD_BASE_URL')
    cache_ttl_seconds: int = Field(default=300, alias='CACHE_TTL_SECONDS')
    rate_limit_max: int = Field(default=60, alias='RATE_LIMIT_MAX')
    rate_limit_window_seconds: int = Field(default=60, alias='RATE_LIMIT_WINDOW_SECONDS')
    http_timeout_seconds: float = Field(default=20.0, alias='HTTP_TIMEOUT_SECONDS')
    http_connect_timeout_seconds: float = Field(default=8.0, alias='HTTP_CONNECT_TIMEOUT_SECONDS')
    http_retries: int = Field(default=3, alias='HTTP_RETRIES')
    max_upstream_concurrency: int = Field(default=12, alias='MAX_UPSTREAM_CONCURRENCY')
    http_max_connections: int = Field(default=100, alias='HTTP_MAX_CONNECTIONS')
    http_max_keepalive_connections: int = Field(default=20, alias='HTTP_MAX_KEEPALIVE_CONNECTIONS')
    default_limit_per_tribunal: int = Field(default=5, alias='DEFAULT_LIMIT_PER_TRIBUNAL')
    max_limit_per_tribunal: int = Field(default=20, alias='MAX_LIMIT_PER_TRIBUNAL')
    user_agent: str = Field(default='JurisprudenciaAPI/4.0 (+https://example.com/contato)', alias='USER_AGENT')
    enable_html_connectors: bool = Field(default=False, alias='ENABLE_HTML_CONNECTORS')
    enable_direct_connectors: bool = Field(default=True, alias='ENABLE_DIRECT_CONNECTORS')
    log_level: Literal['CRITICAL','ERROR','WARNING','INFO','DEBUG'] = Field(default='INFO', alias='LOG_LEVEL')

    @property
    def api_keys_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys if k.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
