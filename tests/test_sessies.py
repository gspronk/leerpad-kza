# tests/test_sessies.py
import json
import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from data.gist import GistClient

SESSIES_FIXTURE = {
    "sessies": [
        {
            "id": "sess-qa2-cloud-20260715",
            "cursus_id": "qa2-cloud",
            "datum": "2026-07-15",
            "tijd": "09:00",
            "locatie": "KZA kantoor",
            "max_deelnemers": 2,
            "deelnemers": ["Anna"]
        }
    ]
}

SESSIE_VOL_FIXTURE = {
    "sessies": [
        {
            "id": "sess-qa2-cloud-20260715",
            "cursus_id": "qa2-cloud",
            "datum": "2026-07-15",
            "tijd": "09:00",
            "locatie": "KZA kantoor",
            "max_deelnemers": 1,
            "deelnemers": ["Anna"]
        }
    ]
}


@pytest.fixture
def mock_gist():
    gist = MagicMock()
    gist.files = {
        "cursussen.json": MagicMock(content='{"profielen":{},"blokken":{},"skills":{},"fases":{}}'),
        "plannen.json": MagicMock(content='{}'),
        "sessies.json": MagicMock(content=json.dumps(SESSIES_FIXTURE)),
    }
    return gist


@pytest.fixture
def client(mock_gist):
    with patch("data.gist.Github") as mock_github:
        mock_github.return_value.get_gist.return_value = mock_gist
        c = GistClient(token="fake-token", gist_id="fake-id")
        c._gist = mock_gist
        return c


# ── Slice 1: read/write sessies ────────────────────────────────────────────

def test_read_sessies_geeft_dict_terug(client):
    result = client.read_sessies()
    assert "sessies" in result
    assert result["sessies"][0]["id"] == "sess-qa2-cloud-20260715"



# ── Slice 2: inschrijven ────────────────────────────────────────────────────

def test_inschrijven_voegt_naam_toe(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    with patch("github.InputFileContent", side_effect=lambda c: MagicMock(content=c)):
        client.inschrijven("sess-qa2-cloud-20260715", "Gerson")
    opgeslagen = json.loads(mock_gist.edit.call_args[1]["files"]["sessies.json"].content)
    deelnemers = opgeslagen["sessies"][0]["deelnemers"]
    assert "Gerson" in deelnemers


def test_inschrijven_faalt_als_vol(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIE_VOL_FIXTURE)
    with pytest.raises(ValueError, match="vol"):
        client.inschrijven("sess-qa2-cloud-20260715", "Gerson")


def test_inschrijven_faalt_als_al_ingeschreven(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    with pytest.raises(ValueError, match="al ingeschreven"):
        client.inschrijven("sess-qa2-cloud-20260715", "Anna")


# ── Slice 3: annuleren ──────────────────────────────────────────────────────

def test_annuleren_voor_deadline_verwijdert_naam(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    vandaag = date(2026, 7, 7)  # 8 dagen voor sessie op 2026-07-15
    with patch("github.InputFileContent", side_effect=lambda c: MagicMock(content=c)):
        client.annuleren("sess-qa2-cloud-20260715", "Anna", vandaag)
    opgeslagen = json.loads(mock_gist.edit.call_args[1]["files"]["sessies.json"].content)
    deelnemers = opgeslagen["sessies"][0]["deelnemers"]
    assert "Anna" not in deelnemers


def test_annuleren_na_deadline_gooit_error(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    vandaag = date(2026, 7, 9)  # 6 dagen voor sessie — na deadline
    with pytest.raises(ValueError, match="deadline"):
        client.annuleren("sess-qa2-cloud-20260715", "Anna", vandaag)


def test_annuleren_niet_ingeschreven_gooit_error(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    vandaag = date(2026, 7, 7)
    with pytest.raises(ValueError, match="niet ingeschreven"):
        client.annuleren("sess-qa2-cloud-20260715", "Gerson", vandaag)


# ── Slice 4: get_sessies_voor_medewerker ────────────────────────────────────

def test_get_sessies_voor_medewerker_filtert_correct(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    sessies = client.get_sessies_voor_medewerker("Anna")
    assert len(sessies) == 1
    assert sessies[0]["id"] == "sess-qa2-cloud-20260715"


def test_get_sessies_voor_medewerker_niet_ingeschreven(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(SESSIES_FIXTURE)
    sessies = client.get_sessies_voor_medewerker("Gerson")
    assert sessies == []
