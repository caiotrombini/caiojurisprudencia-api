# Juris API Modular

API de busca jurisprudencial com prioridade para fontes oficiais, arquitetura modular, cache e rate limit em Redis, `httpx.AsyncClient` compartilhado, controle de concorrência por semáforo, score de confiabilidade por fonte e resposta jurídica normalizada.

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

## Endpoints

- `GET /health`
- `GET /v1/tribunais`
- `GET /v1/search?query=...&tribunais=STJ,TJSP&limite=5`

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
