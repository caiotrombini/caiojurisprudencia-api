from __future__ import annotations

import logging
import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from juris_api.clients.http import request_upstream
from juris_api.core.config import Settings
from juris_api.core.constants import SOURCE_CONFIDENCE
from juris_api.models.domain import ProviderExecution, ServicesContainer
from juris_api.models.schemas import FonteMetadata, ResultadoJuridico
from juris_api.providers.base import BaseProvider
from juris_api.utils.scoring import final_score, lexical_relevance
from juris_api.utils.text import result_identifier, safe_text

logger = logging.getLogger('jurisprudencia_api.providers.tjsp_html')


class TJSPHtmlProvider(BaseProvider):
    provider_name = 'tjsp_html'

    async def search(self, services: ServicesContainer, settings: Settings, tribunal: str, query: str, limit: int) -> ProviderExecution:
        started = time.perf_counter()
        url = f"https://esaj.tjsp.jus.br/cjsg/resultadoCompleta.do?conversationId=&dadosConsulta.pesquisaLivre={quote_plus(query)}"
        response = await request_upstream(services, settings, 'GET', url, provider=self.provider_name)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not response:
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Sem resposta válida do TJSP HTML.')
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.select('.fundocinza1, .resultado')
            confidence = SOURCE_CONFIDENCE[self.provider_name]
            results: list[ResultadoJuridico] = []
            for card in cards[:limit]:
                text = safe_text(card.get_text(' ', strip=True), 4000)
                if not text:
                    continue
                relevance = lexical_relevance(query, text)
                score = final_score(confidence, relevance)
                fonte = FonteMetadata(nome='TJSP HTML', tipo='html_scraping', oficial=True, endpoint=url, score_confiabilidade=confidence, observacao='Fallback HTML sujeito a alteração de layout.')
                results.append(ResultadoJuridico(
                    id_resultado=result_identifier(tribunal, None, text, fonte.nome), tribunal=tribunal, ementa=text, fonte_url=url, fonte=fonte, score_relevancia=relevance, score_final=score, metadados={'provider': self.provider_name}
                ))
            return ProviderExecution(tribunal, self.provider_name, results, latency_ms, 'ok' if results else 'vazio', None if results else 'Scraping do TJSP executado sem resultados.')
        except Exception as exc:
            logger.exception('[tjsp_html] erro ao processar resposta: %s', exc)
            return ProviderExecution(tribunal, self.provider_name, [], latency_ms, 'erro', 'Falha ao interpretar o HTML do TJSP.')
