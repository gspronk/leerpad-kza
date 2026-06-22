# tests/test_gist.py
import pytest
import time
from unittest.mock import MagicMock, patch
from data.gist import GistClient

CURSUSSEN_FIXTURE = {
    "profielen": {"engineer": {"kleur": "#0072B8", "titel": "QA Engineer", "sub": "Technisch"}},
    "blokken": {},
    "skills": {},
    "fases": {}
}

PLANNEN_FIXTURE = {
    "Gerson": {
        "profiel": "engineer",
        "geselecteerd": ["qa2-cloud"],
        "statussen": {"qa2-cloud": "afgerond"},
        "laatst_actief": "2026-05-06"
    }
}

@pytest.fixture
def mock_gist():
    gist = MagicMock()
    gist.files = {
        "cursussen.json": MagicMock(content='{"profielen":{},"blokken":{},"skills":{},"fases":{}}'),
        "plannen.json": MagicMock(content='{}')
    }
    return gist

@pytest.fixture
def client(mock_gist):
    with patch("data.gist.Github") as mock_github:
        mock_github.return_value.get_gist.return_value = mock_gist
        c = GistClient(token="fake-token", gist_id="fake-id")
        c._gist = mock_gist
        return c

def test_read_cursussen_returns_dict(client, mock_gist):
    import json
    mock_gist.files["cursussen.json"].content = json.dumps(CURSUSSEN_FIXTURE)
    result = client.read_cursussen()
    assert result["profielen"]["engineer"]["titel"] == "QA Engineer"

def test_read_cursussen_caches_result(client, mock_gist):
    with patch("data.gist.Github") as mock_github:
        mock_github.return_value.get_gist.return_value = mock_gist
        c = GistClient(token="fake-token", gist_id="fake-id")
        c.read_cursussen()
        c.read_cursussen()
        # Door caching mag de Gist API maar 1x aangeroepen zijn
        assert mock_github.return_value.get_gist.call_count == 1

def test_cache_expires_after_ttl(client, mock_gist):
    import json
    mock_gist.files["cursussen.json"].content = json.dumps(CURSUSSEN_FIXTURE)
    client._cache_ttl = 0.01  # 10ms TTL voor de test
    client.read_cursussen()
    client._cursussen_cache_time = time.time() - 1  # verval cache
    mock_gist.files["cursussen.json"].content = json.dumps({**CURSUSSEN_FIXTURE, "profielen": {}})
    result = client.read_cursussen()
    assert result["profielen"] == {}

def test_write_plannen_invalideert_cache(client, mock_gist):
    client._plannen_cache = {"OudeData": {}}
    client._plannen_cache_time = time.time()
    client.write_plannen(PLANNEN_FIXTURE)
    assert client._plannen_cache is None

def test_write_cursussen_invalideert_cache(client, mock_gist):
    client._cursussen_cache = CURSUSSEN_FIXTURE
    client._cursussen_cache_time = time.time()
    client.write_cursussen(CURSUSSEN_FIXTURE)
    assert client._cursussen_cache is None

def test_naam_matching_case_insensitive(client, mock_gist):
    import json
    mock_gist.files["plannen.json"].content = json.dumps(PLANNEN_FIXTURE)
    plan = client.get_plan("gerson")  # lowercase
    assert plan["profiel"] == "engineer"

def test_naam_matching_trim(client, mock_gist):
    import json
    mock_gist.files["plannen.json"].content = json.dumps(PLANNEN_FIXTURE)
    plan = client.get_plan("  Gerson  ")  # met spaties
    assert plan["profiel"] == "engineer"

def test_get_plan_nieuwe_naam_geeft_lege_dict(client, mock_gist):
    import json
    mock_gist.files["plannen.json"].content = json.dumps(PLANNEN_FIXTURE)
    plan = client.get_plan("NieuweGebruiker")
    assert plan == {}
