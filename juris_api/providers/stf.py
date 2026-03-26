from __future__ import annotations

import logging
import time

from juris_api.clients.http import request_upstream
from juris_api.core.config import Settings
from juris_api.core.constants import SOURCE_CONFIDENCE
from juris_api.models.domain import ProviderExecution, ServicesContainer
from juris_api.models.schemas import FonteMetadata, ResultadoJuridico
from juris_api.providers.base import BaseProvider
from juris_api.utils.dates import normalize_date
from juris_api.utils.scoring import final_score, lexical_relevance, metadata_quality, recency_signal, tribunal_signal
from juris_api.utils.text import clean_url, first_non_empty, infer_document_type, result_identifier, safe_text

logger = logging.getLogger('jurisprudencia_api.providers.stf')


class STFDirectProvider(BaseProvider):
    provider_name = 'stf_direct'

    async def search(self, services: ServicesContainer, settings: Settings, tribunal: str, query: str, limit: int) -> ProviderExecution:
        started = time.perf_counter()
        url = 'https://jurisprudencia.stf.jus.br/api/search/search'
        params = {'query': query, 'sort': 'score', 'size': limit, 'start': 0}
        response = await request_upstream(services, settings, 'GET', url, provider=self.provider_name, params=params)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not response:
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Sem resposta válida do STF.')
        try:
            body = response.json()
            items = body.get('hit', {}).get('item', [])
            confidence = SOURCE_CONFIDENCE[self.provider_name]
            results: list[ResultadoJuridico] = []
            for item in items:
                fields = item.get('fields', {})

                def pick(name: str):
                    value = fields.get(name)
                    if isinstance(value, list) and value:
                        return safe_text(value[0], 4000)
                    return safe_text(value, 4000)

                numero = pick('numeroProcesso')
                ementa = pick('ementa')
                classe = pick('classe')
                orgao = pick('orgaoJulgador')
                relator = pick('ministroRelator')
                data_julgamento = normalize_date(pick('dataDecisao'))
                inteiro_teor_url = clean_url(first_non_empty(pick('urlInteiroTeor'), f"https://jurisprudencia.stf.jus.br/pages/search/juridico/{item.get('id', '')}/false"))
                relevance = lexical_relevance(query, ' '.join(filter(None, [ementa or '', classe or '', orgao or '', relator or ''])))
                meta_score = metadata_quality(
                    has_ementa=bool(ementa),
                    has_relator=bool(relator),
                    has_inteiro_teor=bool(inteiro_teor_url),
                    has_classe=bool(classe),
                    has_orgao=bool(orgao),
                    has_assunto=False,
                )
                score = final_score(
                    confidence,
                    relevance,
                    metadata_score=meta_score,
                    recency_score=recency_signal(data_julgamento),
                    tribunal_score=tribunal_signal(tribunal),
                )
                fonte = FonteMetadata(nome='STF Jurisprudência', tipo='official_portal', oficial=True, endpoint=url, score_confiabilidade=confidence, observacao='Busca direta no portal de jurisprudência do STF.')
                results.append(ResultadoJuridico(
                    id_resultado=result_identifier(tribunal, numero, ementa, fonte.nome), tribunal=tribunal, numero_processo=numero, tipo_documento=infer_document_type(classe, ementa), classe_processual=classe, orgao_julgador=orgao, relator=relator, data_julgamento=data_julgamento, ementa=ementa, inteiro_teor_url=inteiro_teor_url, fonte_url='https://jurisprudencia.stf.jus.br/', fonte=fonte, score_relevancia=relevance, score_final=score, metadados={'provider': self.provider_name, 'item_id': item.get('id')}
                ))
            return ProviderExecution(tribunal, self.provider_name, results, latency_ms, 'ok' if results else 'vazio', None if results else 'Consulta do STF executada sem resultados.')
        except Exception as exc:
            logger.exception('[stf_direct] erro ao processar resposta: %s', exc)
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Falha ao interpretar a resposta do STF.')
