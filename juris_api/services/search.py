from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Optional

from juris_api.core.config import Settings
from juris_api.models.domain import ServicesContainer
from juris_api.models.schemas import DiagnosticoTribunal, JurisprudenciaResponse, ResumoBusca
from juris_api.providers.registry import execute_for_tribunal
from juris_api.services.cache import get_json_cache, set_json_cache
from juris_api.utils.scoring import deduplicate_results
from juris_api.utils.text import sha256_hexdigest
from juris_api.utils.tribunals import parse_tribunais

logger = logging.getLogger('jurisprudencia_api.search')


def _mask_key(api_key: str) -> str:
    digest = sha256_hexdigest(api_key)
    return f"{digest[:8]}...{digest[-4:]}"


async def perform_search(
    *,
    services: ServicesContainer,
    settings: Settings,
    query: str,
    tribunais_raw: Optional[str],
    limite: int,
    api_key: str,
    client_ip: str,
    tipo_documento: Optional[str] = None,
) -> JurisprudenciaResponse:
    tribunais_resolvidos = parse_tribunais(tribunais_raw)
    tipo_documento_normalizado = tipo_documento.strip().lower() if tipo_documento and tipo_documento.strip() else None
    cache_signature = json.dumps({
        'query': query.strip().lower(),
        'tribunais': tribunais_resolvidos,
        'limite': limite,
        'tipo_documento': tipo_documento_normalizado,
        'enable_html_connectors': settings.enable_html_connectors,
        'enable_direct_connectors': settings.enable_direct_connectors,
    }, sort_keys=True, ensure_ascii=False)
    cache_key = f"cache:search:{sha256_hexdigest(cache_signature)}"
    cached = await get_json_cache(services, cache_key)
    if cached:
        cached['resumo']['cache'] = True
        return JurisprudenciaResponse.model_validate(cached)

    search_id = uuid.uuid4().hex
    logger.info('[search_id=%s] busca iniciada | api_key=%s | ip=%s | tribunais=%s | limite=%s | tipo_documento=%s | query=%r', search_id, _mask_key(api_key), client_ip, tribunais_resolvidos, limite, tipo_documento_normalizado, query)
    started = time.perf_counter()
    per_tribunal_tasks = [execute_for_tribunal(services, settings, tribunal, query, limite) for tribunal in tribunais_resolvidos]
    executions_nested = await asyncio.gather(*per_tribunal_tasks, return_exceptions=False)
    executions = [item for sublist in executions_nested for item in sublist]

    diagnostics = []
    aggregated_results = []
    used_sources = []
    warnings = []
    for execution in executions:
        diagnostics.append(DiagnosticoTribunal(
            tribunal=execution.tribunal,
            provider=execution.provider,
            status=execution.status,
            resultados=len(execution.results),
            latencia_ms=execution.latency_ms,
            mensagem=execution.message,
        ))
        if execution.provider not in used_sources:
            used_sources.append(execution.provider)
        aggregated_results.extend(execution.results)
        if execution.message and execution.status in {'erro', 'degradado'}:
            warnings.append(f"{execution.tribunal}/{execution.provider}: {execution.message}")

    unique_results = deduplicate_results(aggregated_results)
    if tipo_documento_normalizado:
        unique_results = [item for item in unique_results if (item.tipo_documento or '').lower() == tipo_documento_normalizado]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response_model = JurisprudenciaResponse(
        query=query,
        resumo=ResumoBusca(
            search_id=search_id,
            total_resultados=len(unique_results),
            tribunais_consultados=tribunais_resolvidos,
            fontes_acionadas=used_sources,
            tempo_resposta_ms=elapsed_ms,
            cache=False,
            avisos=warnings,
        ),
        diagnostico=diagnostics,
        resultados=unique_results,
    )
    await set_json_cache(services, cache_key, response_model, ttl_seconds=settings.cache_ttl_seconds)
    logger.info('[search_id=%s] concluída | resultados=%s | tempo_ms=%s', search_id, len(unique_results), elapsed_ms)
    return response_model
