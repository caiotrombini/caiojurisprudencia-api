from __future__ import annotations

import logging
import time

from juris_api.clients.http import request_upstream
from juris_api.core.config import Settings
from juris_api.core.constants import DATAJUD_ALIASES, SOURCE_CONFIDENCE
from juris_api.models.domain import ProviderExecution, ServicesContainer
from juris_api.models.schemas import FonteMetadata, ResultadoJuridico
from juris_api.providers.base import BaseProvider
from juris_api.utils.dates import normalize_date
from juris_api.utils.scoring import final_score, lexical_relevance
from juris_api.utils.text import extract_name_list, first_non_empty, nested_get, result_identifier, safe_text

logger = logging.getLogger('jurisprudencia_api.providers.datajud')


class DataJudProvider(BaseProvider):
    provider_name = 'datajud'

    async def search(self, services: ServicesContainer, settings: Settings, tribunal: str, query: str, limit: int) -> ProviderExecution:
        started = time.perf_counter()
        alias = DATAJUD_ALIASES.get(tribunal)
        if not alias:
            return ProviderExecution(tribunal, self.provider_name, [], 0, 'erro', 'Tribunal sem alias público DataJud configurado.')
        if not settings.datajud_token:
            return ProviderExecution(tribunal, self.provider_name, [], 0, 'degradado', 'DATAJUD_TOKEN ausente. Provider oficial indisponível.')
        url = f"{settings.datajud_base_url}/api_publica_{alias}/_search"
        headers = {'Authorization': settings.datajud_token, 'Content-Type': 'application/json'}
        payload = {
            'size': limit,
            '_source': {'includes': [
                'numeroProcesso','ementa','orgaoJulgador.nome','orgaoJulgador','classe.nome','classe','assuntos.nome','assuntos',
                'relator.nome','relator','magistradoRelator.nome','dataJulgamento','dataPublicacao','dataHoraUltimaAtualizacao',
                'dataAjuizamento','grau','movimentos.nome','sistema.nome','urlDocumento','urlInteiroTeor','link'
            ]},
            'query': {'multi_match': {'query': query, 'fields': ['numeroProcesso^8','ementa^6','assuntos.nome^3','classe.nome^2','orgaoJulgador.nome^2','movimentos.nome'], 'type': 'best_fields', 'operator': 'or'}}
        }
        response = await request_upstream(services, settings, 'POST', url, provider=self.provider_name, headers=headers, json_body=payload)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not response:
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Sem resposta válida do DataJud.')
        try:
            body = response.json()
            hits = body.get('hits', {}).get('hits', [])
            confidence = SOURCE_CONFIDENCE[self.provider_name]
            results: list[ResultadoJuridico] = []
            for hit in hits:
                src = hit.get('_source', {})
                assuntos = extract_name_list(src.get('assuntos'))
                classe = first_non_empty(nested_get(src, 'classe', 'nome'), src.get('classe'))
                orgao = first_non_empty(nested_get(src, 'orgaoJulgador', 'nome'), src.get('orgaoJulgador'))
                relator = first_non_empty(nested_get(src, 'relator', 'nome'), nested_get(src, 'magistradoRelator', 'nome'), src.get('relator'))
                ementa = safe_text(src.get('ementa'), 4000)
                numero = safe_text(src.get('numeroProcesso'), 80)
                data_julgamento = normalize_date(first_non_empty(src.get('dataJulgamento'), src.get('dataAjuizamento')))
                data_publicacao = normalize_date(first_non_empty(src.get('dataPublicacao'), src.get('dataHoraUltimaAtualizacao')))
                inteiro_teor_url = first_non_empty(src.get('urlInteiroTeor'), src.get('urlDocumento'), src.get('link'))
                relevance = lexical_relevance(query, ' '.join(filter(None, [ementa or '', classe or '', orgao or '', ' '.join(assuntos)])), upstream_score=float(hit.get('_score') or 0.0))
                score = final_score(confidence, relevance)
                fonte = FonteMetadata(nome='DataJud/CNJ', tipo='official_api', oficial=True, endpoint=url, score_confiabilidade=confidence, observacao='API pública oficial do CNJ.')
                results.append(ResultadoJuridico(
                    id_resultado=result_identifier(tribunal, numero, ementa, fonte.nome),
                    tribunal=tribunal,
                    numero_processo=numero,
                    classe_processual=classe,
                    assunto_principal=assuntos[0] if assuntos else None,
                    assuntos=assuntos,
                    orgao_julgador=orgao,
                    relator=relator,
                    data_julgamento=data_julgamento,
                    data_publicacao=data_publicacao,
                    ementa=ementa,
                    inteiro_teor_url=inteiro_teor_url,
                    fonte_url='https://www.cnj.jus.br/sistemas/datajud/',
                    fonte=fonte,
                    score_relevancia=relevance,
                    score_final=score,
                    metadados={'provider': self.provider_name, 'upstream_score': hit.get('_score'), 'grau': src.get('grau'), 'sistema': nested_get(src, 'sistema', 'nome') or src.get('sistema')},
                ))
            return ProviderExecution(tribunal, self.provider_name, results, latency_ms, 'ok' if results else 'vazio', None if results else 'Consulta oficial executada sem resultados.')
        except Exception as exc:
            logger.exception('[datajud/%s] erro ao processar resposta: %s', tribunal, exc)
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Falha ao interpretar a resposta do DataJud.')
