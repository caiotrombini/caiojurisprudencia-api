from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from juris_api.api.deps import get_app_settings, get_services, require_api_key
from juris_api.core.config import Settings
from juris_api.models.domain import ServicesContainer
from juris_api.models.schemas import JurisprudenciaResponse
from juris_api.services.rate_limit import enforce_rate_limit
from juris_api.services.search import perform_search

router = APIRouter(prefix='/v1', tags=['Jurisprudência'])


@router.get('/search', response_model=JurisprudenciaResponse, summary='Buscar jurisprudência')
async def search_jurisprudence(
    request: Request,
    query: str = Query(..., min_length=2, max_length=300, description='Tema, tese ou expressão de busca.'),
    tribunais: Optional[str] = Query(default='STF,STJ,TST,TJSP,TJRJ', description='Lista separada por vírgula. Aceita grupos: TODOS, SUPERIORES, FEDERAIS, ESTADUAIS, TRABALHISTAS, ELEITORAIS, MILITARES.'),
    limite: int = Query(default=5, ge=1, le=20, description='Quantidade máxima por tribunal.'),
    api_key: str = Depends(require_api_key),
    services: ServicesContainer = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
):
    await enforce_rate_limit(services, settings, api_key)
    limite = min(limite, settings.max_limit_per_tribunal)
    response = await perform_search(
        services=services,
        settings=settings,
        query=query,
        tribunais_raw=tribunais,
        limite=limite,
        api_key=api_key,
        client_ip=getattr(request.client, 'host', 'unknown'),
    )
    request.state.search_id = response.resumo.search_id
    return response
