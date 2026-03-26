from __future__ import annotations

import asyncio
import json
import logging
import time
import unicodedata
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

_CACHE_SCHEMA_VERSION = 'docfilter-v2-20260326'


def _mask_key(api_key: str) -> str:
    digest = sha256_hexdigest(api_key)
    return f"{digest[:8]}...{digest[-4:]}"


def _normalize_document_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace('-', '_').replace(' ', '_')
    while '__' in text:
        text = text.replace('__', '_')

    aliases = {
        'acordao': 'acordao',
        'acordaos': 'acordao',
        'decisao_monocratica': 'decisao_monocratica',
        'monocratica': 'decisao_monocratica',
        'sentenca': 'sentenca',
        'despacho': 'despacho',
        'movimentacao': 'movimentacao',
        'movimento': 'movimentacao',
        'andamento': 'movimentacao',
        'processo': 'processo',
    }
    return aliases.get(text, text)


def _compute_candidate_limit(limite: int, tipo_documento_normalizado: Optional[str]) -> int:
    if not tipo_documento_normalizado:
        return limite
    return min(max(limite * 8, 30), 50)


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
    tipo_documento_normalizado = _normalize_document_type(tipo_documento)
    candidate_limit = _compute_candidate_limit(limite, tipo_documento_normalizado)

    cache_signature = json.dumps(
        {
            'search_version': _CACHE_SCHEMA_VERSION,
            'query': query.strip().lower(),
            'tribunais': tribunais_resolvidos,
            'limite': limite,
            'tipo_documento': tipo_documento_normalizado,
            'enable_html_connectors': settings.enable_html_connectors,
            'enable_direct_connectors': settings.enable_direct_connectors,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    cache_key = f"cache:search:{sha256_hexdigest(cache_signature)}"

    cached = await get_json_cache(services, cache_key)
    if cached:
        cached['resumo']['cache'] = True
        return JurisprudenciaResponse.model_validate(cached)

    search_id = uuid.uuid4().hex
    logger.info(
        '[search_id=%s] busca iniciada | api_key=%s | ip=%s | tribunais=%s | limite_final=%s | limite_candidatos=%s | tipo_documento=%s | query=%r',
        search_id,
        _mask_key(api_key),
        client_ip,
        tribunais_resolvidos,
        limite,
        candidate_limit,
        tipo_documento_normalizado,
        query,
    )

    started = time.perf_counter()
    per_tribunal_tasks = [
        execute_for_tribunal(services, settings, tribunal, query, candidate_limit)
        for tribunal in tribunais_resolvidos
    ]
    executions_nested = await asyncio.gather(*per_tribunal_tasks, return_exceptions=False)
    executions = [item for sublist in executions_nested for item in sublist]

    diagnostics: list[DiagnosticoTribunal] = []
    aggregated_results = []
    used_sources: list[str] = []
    warnings: list[str] = []

    for execution in executions:
        diagnostics.append(
            DiagnosticoTribunal(
                tribunal=execution.tribunal,
                provider=execution.provider,
                status=execution.status,
                resultados=len(execution.results),
                latencia_ms=execution.latency_ms,
                mensagem=execution.message,
            )
        )
        if execution.provider not in used_sources:
            used_sources.append(execution.provider)
        aggregated_results.extend(execution.results)
        if execution.message and execution.status in {'erro', 'degradado'}:
            warnings.append(f"{execution.tribunal}/{execution.provider}: {execution.message}")

    unique_results = deduplicate_results(aggregated_results)
    raw_unique_count = len(unique_results)

    filtered_results = unique_results
    if tipo_documento_normalizado:
        filtered_results = [
            item
            for item in unique_results
            if _normalize_document_type(item.tipo_documento) == tipo_documento_normalizado
        ]

        if raw_unique_count > 0 and not filtered_results:
            warnings.append(
                f"Filtro tipo_documento='{tipo_documento_normalizado}' eliminou todos os {raw_unique_count} candidatos normalizados. "
                "Isso indica que o lote bruto retornado pelos providers não continha itens classificados com esse tipo."
            )
        elif len(filtered_results) < raw_unique_count:
            warnings.append(
                f"Filtro tipo_documento='{tipo_documento_normalizado}' reduziu {raw_unique_count} candidatos para {len(filtered_results)} resultado(s)."
            )

    final_results = filtered_results[:limite]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    warnings = list(dict.fromkeys(warnings))

    response_model = JurisprudenciaResponse(
        query=query,
        resumo=ResumoBusca(
            search_id=search_id,
            total_resultados=len(final_results),
            tribunais_consultados=tribunais_resolvidos,
            fontes_acionadas=used_sources,
            tempo_resposta_ms=elapsed_ms,
            cache=False,
            avisos=warnings,
        ),
        diagnostico=diagnostics,
        resultados=final_results,
    )

    await set_json_cache(services, cache_key, response_model, ttl_seconds=settings.cache_ttl_seconds)

    logger.info(
        '[search_id=%s] concluída | candidatos_brutos=%s | candidatos_filtrados=%s | resultados_finais=%s | tempo_ms=%s',
        search_id,
        raw_unique_count,
        len(filtered_results),
        len(final_results),
        elapsed_ms,
    )
    return response_model
