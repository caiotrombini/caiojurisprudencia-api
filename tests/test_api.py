import pytest


@pytest.mark.anyio
async def test_health(client):
    response = await client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['versao'] == '4.1.0'


@pytest.mark.anyio
async def test_tribunais_requires_key(client):
    response = await client.get('/v1/tribunais')
    assert response.status_code == 401
