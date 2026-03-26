# Juris API Modular 4.1

API de busca jurisprudencial com prioridade para fontes oficiais, arquitetura modular, cache e rate limit em Redis, `httpx.AsyncClient` compartilhado, controle de concorrência por semáforo, score de confiabilidade por fonte e resposta jurídica normalizada.

## Melhorias desta revisão

- `API_KEYS` agora aceita string simples, CSV ou JSON array.
- `DATAJUD_TOKEN` é prefixado automaticamente com `APIKey ` quando vier só a chave.
- normalização robusta de datas compactas do DataJud, como `2026022519 -> 2026-02-25`.
- correção de textos com mojibake, como `JustiÃ§a -> Justiça`.
- saneamento do campo `sistema`, evitando valores finais como `Inválido`.
- `tipo_documento` incluído na resposta e filtro opcional em `/v1/search`.
- ranking mais jurídico, considerando relevância textual, completude de metadados, recência e peso institucional do tribunal.
- logs upstream enriquecidos com trecho do corpo da resposta para depuração.

## Estrutura

```text
juris_api/
  api/
    deps.py
    routes/
  clients/
  core/
  models/
  providers/
  services/
  utils/
  main.py
tests/
```

## Subida local

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn juris_api.main:app --reload
```

## Com Docker

```bash
docker compose up --build
```

## Autenticação

Header obrigatório:

```http
X-API-Key: sua-chave
```

`API_KEYS` aceita estes formatos:

```env
API_KEYS=uma-chave
API_KEYS=chave1,chave2,chave3
API_KEYS=["chave1","chave2"]
```

## Endpoints

- `GET /health`
- `GET /v1/tribunais`
- `GET /v1/search?query=...&tribunais=STJ,TJSP&limite=5`
- `GET /v1/search?query=...&tribunais=STJ&limite=5&tipo_documento=acordao`

## Observações técnicas

- O DataJud exige o header `Authorization: APIKey ...`.
- O `AsyncClient` é criado no `lifespan` e reutilizado em toda a aplicação.
- O rate limit usa Redis com script Lua para evitar condição de corrida entre `INCR` e `EXPIRE`.
- O cache é distribuído, JSON e com TTL configurável.
- O STF foi mantido como provider direto separado; o alias público do DataJud na página oficial de endpoints não lista `stf`.
- O scraping HTML do TJSP continua opcional e classificado com score de confiabilidade inferior ao provider oficial.

## Testes

```bash
pytest -q
```
