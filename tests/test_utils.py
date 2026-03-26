from juris_api.core.config import Settings
from juris_api.utils.dates import normalize_date
from juris_api.utils.scoring import final_score, lexical_relevance
from juris_api.utils.text import fix_mojibake, infer_document_type, normalize_source_system
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


def test_settings_api_keys_aceita_string_simples_e_csv():
    settings = Settings(API_KEYS='chave-unica')
    assert settings.api_keys == ['chave-unica']
    settings_csv = Settings(API_KEYS='a,b,c')
    assert settings_csv.api_keys == ['a', 'b', 'c']


def test_settings_datajud_token_prefixado_automaticamente():
    settings = Settings(DATAJUD_TOKEN='abc123')
    assert settings.datajud_token == 'APIKey abc123'


def test_normalize_date_compacta_digitos_extra():
    assert normalize_date('2026022519') == '2026-02-25'
    assert normalize_date('2015102900') == '2015-10-29'


def test_fix_mojibake_corrige_texto_quebrado():
    assert fix_mojibake('JustiÃ§a') == 'Justiça'
    assert fix_mojibake('RAUL ARAÃšJO') == 'RAUL ARAÚJO'


def test_normalize_source_system_saneia_invalido():
    assert normalize_source_system('Inválido') == 'Não informado'


def test_infer_document_type():
    assert infer_document_type('Acórdão', 'Responsabilidade civil') == 'acordao'
    assert infer_document_type('Sentença em ação indenizatória') == 'sentenca'
