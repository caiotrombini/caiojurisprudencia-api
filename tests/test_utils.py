from juris_api.utils.scoring import final_score, lexical_relevance
from juris_api.utils.tribunals import parse_tribunais


def test_parse_tribunais_expande_grupo():
    tribunais = parse_tribunais('SUPERIORES')
    assert 'STF' in tribunais
    assert 'STJ' in tribunais


def test_lexical_relevance_tem_sinal_positivo():
    score = lexical_relevance('dano moral consumidor', 'ação de dano moral em relação de consumo')
    assert score > 0


def test_final_score_intervalo():
    score = final_score(0.99, 0.50)
    assert 0 <= score <= 1
