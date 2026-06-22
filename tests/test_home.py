# tests/test_home.py
from datetime import date
from views.home import _bepaal_editie_kaart, _bepaal_aanbevelingen

VANDAAG = date(2026, 6, 22)

EDITIE_INGESCHREVEN = {
    "id": "edit-qa2-cloud-202607",
    "cursus_id": "qa2-cloud",
    "naam": "Editie juli",
    "max_deelnemers": 12,
    "deelnemers": ["Gerson"],
    "sessies": [{"datum": "2026-07-15", "tijd": "09:00", "locatie": "KZA kantoor"}],
}

EDITIE_LEERPLAN = {
    "id": "edit-sec-pen-202608",
    "cursus_id": "sec-pentest",
    "naam": "Editie aug",
    "max_deelnemers": 12,
    "deelnemers": [],
    "sessies": [{"datum": "2026-08-01", "tijd": "09:00", "locatie": "KZA kantoor"}],
}

EDITIE_KERN = {
    "id": "edit-qa-basis-202609",
    "cursus_id": "qa-basis",
    "naam": "Editie sep",
    "max_deelnemers": 12,
    "deelnemers": [],
    "sessies": [{"datum": "2026-09-01", "tijd": "09:00", "locatie": "KZA kantoor"}],
}

EDITIE_VERLEDEN = {
    "id": "edit-old-202601",
    "cursus_id": "qa2-cloud",
    "naam": "Editie jan",
    "max_deelnemers": 12,
    "deelnemers": ["Gerson"],
    "sessies": [{"datum": "2026-01-01", "tijd": "09:00", "locatie": "KZA kantoor"}],
}

PLAN = {
    "profiel": "engineer",
    "geselecteerd": ["qa2-cloud", "sec-pentest"],
    "statussen": {},
}

KERN_IDS = {"qa2-cloud", "qa-basis"}

DATA_AANBEVELINGEN = {
    "blokken": {
        "engineer": [
            {
                "sectie": "Basis",
                "items": [
                    {"id": "qa-basis",  "naam": "QA Basis",  "kern": True,  "icon": "🧪"},
                    {"id": "qa-tools",  "naam": "QA Tools",  "kern": True,  "icon": "🔧"},
                    {"id": "qa-extra",  "naam": "QA Extra",  "kern": False, "icon": "➕"},
                    {"id": "qa-adv",    "naam": "QA Adv",    "kern": True,  "icon": "🚀"},
                    {"id": "qa-sec",    "naam": "QA Sec",    "kern": True,  "icon": "🔒"},
                ],
            }
        ]
    },
}


# ── _bepaal_editie_kaart ──────────────────────────────────────────────────────

def test_ingeschreven_geeft_editie_en_true():
    editie, is_inschr = _bepaal_editie_kaart(PLAN, "Gerson", [EDITIE_INGESCHREVEN], KERN_IDS, VANDAAG)
    assert editie["id"] == "edit-qa2-cloud-202607"
    assert is_inschr is True


def test_leerplan_geeft_editie_en_false():
    editie, is_inschr = _bepaal_editie_kaart(PLAN, "Anna", [EDITIE_LEERPLAN], KERN_IDS, VANDAAG)
    assert editie["id"] == "edit-sec-pen-202608"
    assert is_inschr is False


def test_kern_geeft_editie_en_false():
    plan_leeg = {**PLAN, "geselecteerd": []}
    editie, is_inschr = _bepaal_editie_kaart(plan_leeg, "Anna", [EDITIE_KERN], KERN_IDS, VANDAAG)
    assert editie["id"] == "edit-qa-basis-202609"
    assert is_inschr is False


def test_geen_relevante_editie_geeft_none():
    editie, is_inschr = _bepaal_editie_kaart(PLAN, "Anna", [], set(), VANDAAG)
    assert editie is None
    assert is_inschr is False


def test_verleden_editie_wordt_overgeslagen():
    editie, _ = _bepaal_editie_kaart(PLAN, "Gerson", [EDITIE_VERLEDEN], KERN_IDS, VANDAAG)
    assert editie is None


def test_editie_vandaag_wordt_meegenomen():
    editie_vandaag = {
        "id": "edit-today",
        "cursus_id": "qa2-cloud",
        "naam": "Editie vandaag",
        "max_deelnemers": 12,
        "deelnemers": ["Gerson"],
        "sessies": [{"datum": "2026-06-22", "tijd": "09:00", "locatie": "KZA kantoor"}],
    }
    editie, is_inschr = _bepaal_editie_kaart(PLAN, "Gerson", [editie_vandaag], KERN_IDS, VANDAAG)
    assert editie["id"] == "edit-today"
    assert is_inschr is True


def test_ingeschreven_heeft_prioriteit_boven_leerplan():
    editie, is_inschr = _bepaal_editie_kaart(
        PLAN, "Gerson", [EDITIE_LEERPLAN, EDITIE_INGESCHREVEN], KERN_IDS, VANDAAG
    )
    assert editie["id"] == "edit-qa2-cloud-202607"
    assert is_inschr is True


def test_leerplan_heeft_prioriteit_boven_kern():
    plan_met_sec = {**PLAN, "geselecteerd": ["sec-pentest"]}
    editie, _ = _bepaal_editie_kaart(
        plan_met_sec, "Anna", [EDITIE_KERN, EDITIE_LEERPLAN], KERN_IDS, VANDAAG
    )
    assert editie["id"] == "edit-sec-pen-202608"


# ── _bepaal_aanbevelingen ─────────────────────────────────────────────────────

def test_aanbevelingen_geeft_kern_niet_geselecteerd():
    plan = {"profiel": "engineer", "geselecteerd": [], "statussen": {}}
    resultaat = _bepaal_aanbevelingen(plan, DATA_AANBEVELINGEN)
    ids = [item["id"] for item in resultaat]
    assert "qa-basis" in ids
    assert "qa-extra" not in ids  # niet kern


def test_aanbevelingen_max_3():
    plan = {"profiel": "engineer", "geselecteerd": [], "statussen": {}}
    resultaat = _bepaal_aanbevelingen(plan, DATA_AANBEVELINGEN)
    assert len(resultaat) == 3


def test_aanbevelingen_slaat_geselecteerde_over():
    plan = {"profiel": "engineer", "geselecteerd": ["qa-basis"], "statussen": {}}
    resultaat = _bepaal_aanbevelingen(plan, DATA_AANBEVELINGEN)
    ids = [item["id"] for item in resultaat]
    assert "qa-basis" not in ids


def test_aanbevelingen_leeg_als_alle_kern_geselecteerd():
    plan = {
        "profiel": "engineer",
        "geselecteerd": ["qa-basis", "qa-tools", "qa-adv", "qa-sec"],
        "statussen": {},
    }
    assert _bepaal_aanbevelingen(plan, DATA_AANBEVELINGEN) == []


def test_aanbevelingen_onbekend_profiel_geeft_lege_lijst():
    plan = {"profiel": "onbekend", "geselecteerd": [], "statussen": {}}
    assert _bepaal_aanbevelingen(plan, DATA_AANBEVELINGEN) == []
