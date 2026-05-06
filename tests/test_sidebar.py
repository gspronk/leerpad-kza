# tests/test_sidebar.py
import pytest
from unittest.mock import MagicMock, patch
from components.sidebar import normalize_naam, kern_ids_voor_profiel

CURSUSSEN_FIXTURE = {
    "blokken": {
        "engineer": [
            {"sectie": "Fundament", "badge": "F", "items": [
                {"id": "qa2-cloud", "kern": True},
                {"id": "qa2-linux", "kern": False},
                {"id": "ta-api",    "kern": True},
            ]}
        ]
    }
}

def test_normalize_naam_lowercase():
    assert normalize_naam("GERSON") == "gerson"

def test_normalize_naam_trim():
    assert normalize_naam("  Gerson  ") == "gerson"

def test_normalize_naam_mixed():
    assert normalize_naam(" Anna ") == "anna"

def test_kern_ids_voor_profiel():
    ids = kern_ids_voor_profiel(CURSUSSEN_FIXTURE, "engineer")
    assert "qa2-cloud" in ids
    assert "ta-api" in ids
    assert "qa2-linux" not in ids

def test_kern_ids_onbekend_profiel():
    ids = kern_ids_voor_profiel(CURSUSSEN_FIXTURE, "onbekend")
    assert ids == []
