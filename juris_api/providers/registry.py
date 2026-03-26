from __future__ import annotations

from juris_api.core.constants import DATAJUD_ALIASES
from juris_api.models.domain import ProviderExecution, ServicesContainer
from juris_api.providers.datajud import DataJudProvider
from juris_api.providers.stf import STFDirectProvider
from juris_api.providers.tjsp_html import TJSPHtmlProvider
from juris_api.providers.tst import TSTDirectProvider
from juris_api.core.config import Settings


datajud_provider = DataJudProvider()
stf_provider = STFDirectProvider()
tst_provider = TSTDirectProvider()
tjsp_html_provider = TJSPHtmlProvider()


async def execute_for_tribunal(services: ServicesContainer, settings: Settings, tribunal: str, query: str, limit: int) -> list[ProviderExecution]:
    tribunal = tribunal.upper()
    executions: list[ProviderExecution] = []

    if tribunal == 'STF':
        if settings.enable_direct_connectors:
            executions.append(await stf_provider.search(services, settings, tribunal, query, limit))
        else:
            executions.append(ProviderExecution(tribunal, 'stf_direct', [], 0, 'degradado', 'Provider direto do STF desabilitado por configuração.'))
        return executions

    if tribunal == 'TST' and settings.enable_direct_connectors:
        direct = await tst_provider.search(services, settings, tribunal, query, limit)
        executions.append(direct)
        if direct.status in {'erro', 'vazio'} and tribunal in DATAJUD_ALIASES:
            executions.append(await datajud_provider.search(services, settings, tribunal, query, limit))
        return executions

    if tribunal == 'TJSP':
        official = await datajud_provider.search(services, settings, tribunal, query, limit)
        executions.append(official)
        if settings.enable_html_connectors and official.status in {'erro', 'vazio'}:
            executions.append(await tjsp_html_provider.search(services, settings, tribunal, query, limit))
        return executions

    if tribunal in DATAJUD_ALIASES:
        executions.append(await datajud_provider.search(services, settings, tribunal, query, limit))
        return executions

    executions.append(ProviderExecution(tribunal, 'unmapped', [], 0, 'erro', 'Tribunal suportado semanticamente, mas sem provider ativo.'))
    return executions
