# tests/test_edities.py
import json
import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from data.gist import GistClient

EDITIE = {
    "id": "edit-qa2-cloud-202607",
    "cursus_id": "qa2-cloud",
    "naam": "Editie juli 2026",
    "max_deelnemers": 2,
    "deelnemers": ["Anna"],
    "sessies": [
        {"datum": "2026-07-15", "tijd": "09:00", "locatie": "KZA kantoor"},
        {"datum": "2026-07-16", "tijd": "09:00", "locatie": "KZA kantoor"},
    ],
}

EDITIES_FIXTURE = {"edities": [EDITIE]}

EDITIE_VOL = {**EDITIE, "max_deelnemers": 1}
EDITIES_VOL_FIXTURE = {"edities": [EDITIE_VOL]}


@pytest.fixture
def mock_gist():
    gist = MagicMock()
    gist.files = {
        "cursussen.json": MagicMock(content='{"profielen":{},"blokken":{},"skills":{},"fases":{}}'),
        "plannen.json": MagicMock(content="{}"),
        "sessies.json": MagicMock(content=json.dumps(EDITIES_FIXTURE)),
    }
    return gist


@pytest.fixture
def client(mock_gist):
    with patch("data.gist.Github") as mock_github:
        mock_github.return_value.get_gist.return_value = mock_gist
        c = GistClient(token="fake-token", gist_id="fake-id")
        c._gist = mock_gist
        return c


# ── Slice 1: read_edities ──────────────────────────────────────────────────

def test_read_edities_geeft_dict_terug(client):
    result = client.read_edities()
    assert "edities" in result
    assert result["edities"][0]["id"] == "edit-qa2-cloud-202607"


# ── Slice 2: inschrijven_editie ────────────────────────────────────────────

def test_inschrijven_editie_voegt_naam_toe(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    with patch("github.InputFileContent", side_effect=lambda c: MagicMock(content=c)):
        client.inschrijven_editie("edit-qa2-cloud-202607", "Gerson")
    opgeslagen = json.loads(mock_gist.edit.call_args[1]["files"]["sessies.json"].content)
    assert "Gerson" in opgeslagen["edities"][0]["deelnemers"]


def test_inschrijven_editie_faalt_als_vol(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_VOL_FIXTURE)
    with pytest.raises(ValueError, match="vol"):
        client.inschrijven_editie("edit-qa2-cloud-202607", "Gerson")


def test_inschrijven_editie_faalt_als_al_ingeschreven(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    with pytest.raises(ValueError, match="al ingeschreven"):
        client.inschrijven_editie("edit-qa2-cloud-202607", "Anna")


# ── Slice 3: annuleren_editie ──────────────────────────────────────────────

def test_annuleren_editie_voor_deadline_verwijdert_naam(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    vandaag = date(2026, 7, 7)  # 8 dagen voor eerste sessie (2026-07-15)
    with patch("github.InputFileContent", side_effect=lambda c: MagicMock(content=c)):
        client.annuleren_editie("edit-qa2-cloud-202607", "Anna", vandaag)
    opgeslagen = json.loads(mock_gist.edit.call_args[1]["files"]["sessies.json"].content)
    assert "Anna" not in opgeslagen["edities"][0]["deelnemers"]


def test_annuleren_editie_na_deadline_gooit_error(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    vandaag = date(2026, 7, 9)  # 6 dagen voor eerste sessie — na deadline
    with pytest.raises(ValueError, match="deadline"):
        client.annuleren_editie("edit-qa2-cloud-202607", "Anna", vandaag)


def test_annuleren_editie_niet_ingeschreven_gooit_error(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    vandaag = date(2026, 7, 7)
    with pytest.raises(ValueError, match="niet ingeschreven"):
        client.annuleren_editie("edit-qa2-cloud-202607", "Gerson", vandaag)


# ── Slice 4: get_edities_voor_medewerker ──────────────────────────────────

def test_get_edities_voor_medewerker_filtert_correct(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    edities = client.get_edities_voor_medewerker("Anna")
    assert len(edities) == 1
    assert edities[0]["id"] == "edit-qa2-cloud-202607"


def test_get_edities_voor_medewerker_niet_ingeschreven(client, mock_gist):
    mock_gist.files["sessies.json"].content = json.dumps(EDITIES_FIXTURE)
    edities = client.get_edities_voor_medewerker("Gerson")
    assert edities == []
