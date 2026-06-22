# tests/test_beheer_logic.py
import copy
import pytest
from views.beheer import _update_item_in_data, _verwijder_item_uit_data, _editie_naam_default

DATA = {
    "blokken": {
        "engineer": [
            {
                "sectie": "Cloud",
                "items": [
                    {"id": "qa2-cloud",  "naam": "Cloud Basics", "kern": True},
                    {"id": "qa2-docker", "naam": "Docker",       "kern": False},
                ],
            }
        ],
        "security": [
            {
                "sectie": "Pentest",
                "items": [
                    {"id": "sec-pentest", "naam": "Pentest Intro", "kern": True},
                ],
            }
        ],
    }
}


# ── _update_item_in_data ──────────────────────────────────────────────────────

def test_update_item_wijzigt_naam():
    data = copy.deepcopy(DATA)
    _update_item_in_data(data, "qa2-cloud", {"naam": "Cloud Advanced"})
    item = data["blokken"]["engineer"][0]["items"][0]
    assert item["naam"] == "Cloud Advanced"


def test_update_item_laat_andere_velden_intact():
    data = copy.deepcopy(DATA)
    _update_item_in_data(data, "qa2-cloud", {"naam": "Nieuw"})
    item = data["blokken"]["engineer"][0]["items"][0]
    assert item["kern"] is True


def test_update_item_werkt_in_ander_profiel():
    data = copy.deepcopy(DATA)
    _update_item_in_data(data, "sec-pentest", {"kern": False})
    item = data["blokken"]["security"][0]["items"][0]
    assert item["kern"] is False


def test_update_item_onbekend_id_geen_fout():
    data = copy.deepcopy(DATA)
    _update_item_in_data(data, "bestaat-niet", {"naam": "X"})
    # Geen uitzondering, data ongewijzigd
    assert len(data["blokken"]["engineer"][0]["items"]) == 2


# ── _verwijder_item_uit_data ──────────────────────────────────────────────────

def test_verwijder_item_verwijdert_correct():
    data = copy.deepcopy(DATA)
    _verwijder_item_uit_data(data, "qa2-docker")
    items = data["blokken"]["engineer"][0]["items"]
    assert len(items) == 1
    assert items[0]["id"] == "qa2-cloud"


def test_verwijder_item_laat_andere_profielen_intact():
    data = copy.deepcopy(DATA)
    _verwijder_item_uit_data(data, "qa2-cloud")
    sec_items = data["blokken"]["security"][0]["items"]
    assert len(sec_items) == 1


def test_verwijder_item_onbekend_id_geen_fout():
    data = copy.deepcopy(DATA)
    _verwijder_item_uit_data(data, "bestaat-niet")
    assert len(data["blokken"]["engineer"][0]["items"]) == 2


def test_verwijder_item_in_ander_profiel():
    data = copy.deepcopy(DATA)
    _verwijder_item_uit_data(data, "sec-pentest")
    assert data["blokken"]["security"][0]["items"] == []


# ── _editie_naam_default ──────────────────────────────────────────────────────

@pytest.mark.parametrize("datum,verwacht", [
    ("2026-01-15", "Editie januari 2026"),
    ("2026-03-01", "Editie maart 2026"),
    ("2026-07-20", "Editie juli 2026"),
    ("2026-12-05", "Editie december 2026"),
])
def test_editie_naam_default_maanden(datum, verwacht):
    assert _editie_naam_default("qa2-cloud", datum) == verwacht
