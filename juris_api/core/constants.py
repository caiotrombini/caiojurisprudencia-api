from __future__ import annotations

DATAJUD_ALIASES: dict[str, str] = {
    'STJ': 'stj', 'TST': 'tst', 'TSE': 'tse', 'STM': 'stm',
    'TRF1': 'trf1', 'TRF2': 'trf2', 'TRF3': 'trf3', 'TRF4': 'trf4', 'TRF5': 'trf5', 'TRF6': 'trf6',
    'TJAC': 'tjac', 'TJAL': 'tjal', 'TJAM': 'tjam', 'TJAP': 'tjap', 'TJBA': 'tjba', 'TJCE': 'tjce',
    'TJDF': 'tjdft', 'TJES': 'tjes', 'TJGO': 'tjgo', 'TJMA': 'tjma', 'TJMG': 'tjmg', 'TJMS': 'tjms',
    'TJMT': 'tjmt', 'TJPA': 'tjpa', 'TJPB': 'tjpb', 'TJPE': 'tjpe', 'TJPI': 'tjpi', 'TJPR': 'tjpr',
    'TJRJ': 'tjrj', 'TJRN': 'tjrn', 'TJRO': 'tjro', 'TJRR': 'tjrr', 'TJRS': 'tjrs', 'TJSC': 'tjsc',
    'TJSE': 'tjse', 'TJSP': 'tjsp', 'TJTO': 'tjto',
    'TRT1': 'trt1', 'TRT2': 'trt2', 'TRT3': 'trt3', 'TRT4': 'trt4', 'TRT5': 'trt5', 'TRT6': 'trt6',
    'TRT7': 'trt7', 'TRT8': 'trt8', 'TRT9': 'trt9', 'TRT10': 'trt10', 'TRT11': 'trt11', 'TRT12': 'trt12',
    'TRT13': 'trt13', 'TRT14': 'trt14', 'TRT15': 'trt15', 'TRT16': 'trt16', 'TRT17': 'trt17', 'TRT18': 'trt18',
    'TRT19': 'trt19', 'TRT20': 'trt20', 'TRT21': 'trt21', 'TRT22': 'trt22', 'TRT23': 'trt23', 'TRT24': 'trt24',
    'TRE-AC': 'tre-ac', 'TRE-AL': 'tre-al', 'TRE-AM': 'tre-am', 'TRE-AP': 'tre-ap', 'TRE-BA': 'tre-ba',
    'TRE-CE': 'tre-ce', 'TRE-DF': 'tre-dft', 'TRE-ES': 'tre-es', 'TRE-GO': 'tre-go', 'TRE-MA': 'tre-ma',
    'TRE-MG': 'tre-mg', 'TRE-MS': 'tre-ms', 'TRE-MT': 'tre-mt', 'TRE-PA': 'tre-pa', 'TRE-PB': 'tre-pb',
    'TRE-PE': 'tre-pe', 'TRE-PI': 'tre-pi', 'TRE-PR': 'tre-pr', 'TRE-RJ': 'tre-rj', 'TRE-RN': 'tre-rn',
    'TRE-RO': 'tre-ro', 'TRE-RR': 'tre-rr', 'TRE-RS': 'tre-rs', 'TRE-SC': 'tre-sc', 'TRE-SE': 'tre-se',
    'TRE-SP': 'tre-sp', 'TRE-TO': 'tre-to',
    'TJMMG': 'tjmmg', 'TJMRS': 'tjmrs', 'TJMSP': 'tjmsp',
}

TRIBUNAL_GROUPS: dict[str, list[str]] = {
    'SUPERIORES': ['STF', 'STJ', 'TST', 'TSE', 'STM'],
    'FEDERAIS': ['TRF1', 'TRF2', 'TRF3', 'TRF4', 'TRF5', 'TRF6'],
    'ESTADUAIS': ['TJAC','TJAL','TJAM','TJAP','TJBA','TJCE','TJDF','TJES','TJGO','TJMA','TJMG','TJMS','TJMT','TJPA','TJPB','TJPE','TJPI','TJPR','TJRJ','TJRN','TJRO','TJRR','TJRS','TJSC','TJSE','TJSP','TJTO'],
    'TRABALHISTAS': [f'TRT{i}' for i in range(1, 25)],
    'ELEITORAIS': ['TRE-AC','TRE-AL','TRE-AM','TRE-AP','TRE-BA','TRE-CE','TRE-DF','TRE-ES','TRE-GO','TRE-MA','TRE-MG','TRE-MS','TRE-MT','TRE-PA','TRE-PB','TRE-PE','TRE-PI','TRE-PR','TRE-RJ','TRE-RN','TRE-RO','TRE-RR','TRE-RS','TRE-SC','TRE-SE','TRE-SP','TRE-TO'],
    'MILITARES': ['STM','TJMMG','TJMRS','TJMSP'],
}
TRIBUNAL_GROUPS['TODOS'] = list(dict.fromkeys(
    TRIBUNAL_GROUPS['SUPERIORES'] + TRIBUNAL_GROUPS['FEDERAIS'] + TRIBUNAL_GROUPS['ESTADUAIS'] + TRIBUNAL_GROUPS['TRABALHISTAS'] + TRIBUNAL_GROUPS['ELEITORAIS'] + TRIBUNAL_GROUPS['MILITARES']
))
SUPPORTED_TRIBUNAIS = TRIBUNAL_GROUPS['TODOS']

SOURCE_CONFIDENCE: dict[str, float] = {
    'datajud': 0.99,
    'stf_direct': 0.95,
    'tst_direct': 0.95,
    'tjsp_html': 0.72,
    'derived_link': 0.40,
}

RETRYABLE_STATUSES = {408, 425, 429, 500, 502, 503, 504}
