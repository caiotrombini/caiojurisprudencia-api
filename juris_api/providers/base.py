from __future__ import annotations

from abc import ABC, abstractmethod

from juris_api.core.config import Settings
from juris_api.models.domain import ProviderExecution, ServicesContainer


class BaseProvider(ABC):
    provider_name: str

    @abstractmethod
    async def search(self, services: ServicesContainer, settings: Settings, tribunal: str, query: str, limit: int) -> ProviderExecution:
        raise NotImplementedError
