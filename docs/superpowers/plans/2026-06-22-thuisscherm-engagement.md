# Thuisscherm + Engagement — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voeg een persoonlijk thuisscherm toe als eerste tab, met voortgangsbanner, editie-kaart, mijlpaalkaart, aanbevelingen, en toast-notificaties bij het behalen van mijlpalen.

**Architecture:** Twee nieuwe modules (`data/milestones.py`, `views/home.py`) en kleine uitbreidingen op `app.py` en `views/mijn_plan.py`. Alle logica is pure Python (testbaar), UI-functies bevatten alleen Streamlit-aanroepen (niet unit-testbaar). Datamodel (`cursussen.json`, `plannen.json`, `sessies.json`) is ongewijzigd.

**Tech Stack:** Python 3.11, Streamlit, PyGithub. Tests via pytest (stijl: zie `tests/test_beheer_logic.py`). Linting via ruff.

---

## Bestandsoverzicht

| Actie | Bestand |
|---|---|
| Nieuw | `data/milestones.py` |
| Nieuw | `views/home.py` |
| Nieuw | `tests/test_milestones.py` |
| Nieuw | `tests/test_home.py` |
| Wijzig | `app.py` — Home als eerste tab |
| Wijzig | `views/mijn_plan.py` — toast bij mijlpaal |

---

## Task 1: `data/milestones.py` — Mijlpaalberekening (TDD)

**Files:**
- Create: `data/milestones.py`
- Create: `tests/test_milestones.py`

- [ ] **Stap 1: Maak de stub aan**

```python
# data/milestones.py
from dataclasses import dataclass


@dataclass
class Mijlpaal:
    id: str
    label: str
    icon: str
    prioriteit: int  # hogere waarde = hogere mijlpaal


def bereken_mijlpalen(plan: dict, data: dict) -> list:
    return []


def hoogste_mijlpaal(plan: dict, data: dict):
    return None
```

- [ ] **Stap 2: Schrijf de falende tests**

```python
# tests/test_milestones.py
import pytest
from data.milestones import bereken_mijlpalen, hoogste_mijlpaal, Mijlpaal

DATA = {
    "blokken": {
        "engineer": [
            {
                "sectie": "Basis",
                "items": [
                    {"id": "qa-basis", "naam": "QA Basis", "kern": True},
                    {"id": "qa-tools", "naam": "QA Tools", "kern": True},
                    {"id": "qa-extra", "naam": "QA Extra", "kern": False},
                ],
            }
        ]
    },
    "fases": {
        "engineer": [
            {"num": 1, "naam": "Fundament", "items": ["qa-basis", "qa-tools"]},
            {"num": 2, "naam": "Verdieping", "items": ["qa-extra"]},
        ]
    },
}

PLAN_LEEG = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools"],
    "statussen": {},
}

PLAN_EEN_AFGEROND = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond"},
}

PLAN_FASE1_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond"},
}

PLAN_KERN_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond", "qa-extra": "gepland"},
}

PLAN_ALLES_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond", "qa-extra": "afgerond"},
}


def test_geen_mijlpalen_als_niets_afgerond():
    assert bereken_mijlpalen(PLAN_LEEG, DATA) == []


def test_eerste_cursus_bij_een_afgerond():
    ids = [m.id for m in bereken_mijlpalen(PLAN_EEN_AFGEROND, DATA)]
    assert "eerste_cursus" in ids


def test_fase1_voltooid_bevat_beide_mijlpalen():
    ids = [m.id for m in bereken_mijlpalen(PLAN_FASE1_VOLTOOID, DATA)]
    assert "eerste_cursus" in ids
    assert "fase_1_voltooid" in ids


def test_fase2_niet_voltooid_als_item_ontbreekt():
    ids = [m.id for m in bereken_mijlpalen(PLAN_FASE1_VOLTOOID, DATA)]
    assert "fase_2_voltooid" not in ids


def test_alle_kern_voltooid():
    ids = [m.id for m in bereken_mijlpalen(PLAN_KERN_VOLTOOID, DATA)]
    assert "alle_kern" in ids


def test_leerplan_volledig():
    ids = [m.id for m in bereken_mijlpalen(PLAN_ALLES_VOLTOOID, DATA)]
    assert "leerplan_volledig" in ids


def test_gesorteerd_op_prioriteit_laag_naar_hoog():
    resultaat = bereken_mijlpalen(PLAN_ALLES_VOLTOOID, DATA)
    prio = [m.prioriteit for m in resultaat]
    assert prio == sorted(prio)


def test_hoogste_mijlpaal_geeft_leerplan_volledig():
    m = hoogste_mijlpaal(PLAN_ALLES_VOLTOOID, DATA)
    assert m.id == "leerplan_volledig"


def test_hoogste_mijlpaal_none_als_niets_afgerond():
    assert hoogste_mijlpaal(PLAN_LEEG, DATA) is None


def test_fase_zonder_items_niet_voltooid():
    data_leeg = {
        **DATA,
        "fases": {"engineer": [{"num": 1, "naam": "Leeg", "items": []}]},
    }
    ids = [m.id for m in bereken_mijlpalen(PLAN_EEN_AFGEROND, data_leeg)]
    assert "fase_1_voltooid" not in ids
```

- [ ] **Stap 3: Draai de tests — verwacht FAIL**

```
pytest tests/test_milestones.py -v
```

Verwacht: alle tests FAIL (functies retourneren lege lijst / None).

- [ ] **Stap 4: Implementeer `data/milestones.py`**

```python
# data/milestones.py
from dataclasses import dataclass


@dataclass
class Mijlpaal:
    id: str
    label: str
    icon: str
    prioriteit: int


def bereken_mijlpalen(plan: dict, data: dict) -> list:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    afgerond = {iid for iid, s in plan.get("statussen", {}).items() if s == "afgerond"}
    resultaat = []

    if len(afgerond) >= 1:
        resultaat.append(Mijlpaal(
            id="eerste_cursus",
            label="Eerste cursus afgerond",
            icon="🎉",
            prioriteit=1,
        ))

    for fase in data.get("fases", {}).get(profiel, []):
        fase_items = set(fase.get("items", []))
        if fase_items and fase_items.issubset(afgerond):
            resultaat.append(Mijlpaal(
                id=f"fase_{fase['num']}_voltooid",
                label=f"Fase {fase['num']} voltooid — {fase['naam']}",
                icon="🏅",
                prioriteit=10 + fase["num"],
            ))

    kern_ids = {
        item["id"]
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
        if item.get("kern")
    }
    if kern_ids and kern_ids.issubset(afgerond):
        resultaat.append(Mijlpaal(
            id="alle_kern",
            label="Alle kern-cursussen afgerond",
            icon="⭐",
            prioriteit=50,
        ))

    if geselecteerd and geselecteerd.issubset(afgerond):
        resultaat.append(Mijlpaal(
            id="leerplan_volledig",
            label="Leerplan volledig afgerond",
            icon="🏆",
            prioriteit=100,
        ))

    return sorted(resultaat, key=lambda m: m.prioriteit)


def hoogste_mijlpaal(plan: dict, data: dict):
    mijlpalen = bereken_mijlpalen(plan, data)
    return mijlpalen[-1] if mijlpalen else None
```

- [ ] **Stap 5: Draai de tests — verwacht PASS**

```
pytest tests/test_milestones.py -v
```

Verwacht: alle 10 tests PASS.

- [ ] **Stap 6: Lint**

```
ruff check data/milestones.py tests/test_milestones.py
```

Verwacht: geen fouten.

- [ ] **Stap 7: Commit**

```
git add data/milestones.py tests/test_milestones.py
git commit -m "feat: voeg milestone-berekening toe (bereken_mijlpalen, hoogste_mijlpaal)"
```

---

## Task 2: `views/home.py` — Helperfuncties (TDD)

**Files:**
- Create: `views/home.py` (stub + helpers)
- Create: `tests/test_home.py`

- [ ] **Stap 1: Maak de stub aan**

```python
# views/home.py
from datetime import date


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    pass


def _bepaal_editie_kaart(
    plan: dict,
    naam: str,
    alle_edities: list,
    kern_cursus_ids: set,
    vandaag: date,
) -> tuple:
    return None, False


def _bepaal_aanbevelingen(plan: dict, data: dict, max_items: int = 3) -> list:
    return []


def _bepaal_huidige_fase(plan: dict, data: dict):
    return None


def _bepaal_volgende_stap(plan: dict, cursus_lookup: dict):
    return None
```

- [ ] **Stap 2: Schrijf de falende tests**

```python
# tests/test_home.py
import pytest
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
    assert len(resultaat) <= 3


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
```

- [ ] **Stap 3: Draai de tests — verwacht FAIL**

```
pytest tests/test_home.py -v
```

Verwacht: alle 11 tests FAIL (stubs retourneren standaardwaarden).

- [ ] **Stap 4: Implementeer `_bepaal_editie_kaart` en `_bepaal_aanbevelingen`**

Vervang de stub-implementaties in `views/home.py`:

```python
def _bepaal_editie_kaart(
    plan: dict,
    naam: str,
    alle_edities: list,
    kern_cursus_ids: set,
    vandaag: date,
) -> tuple:
    geselecteerd = set(plan.get("geselecteerd", []))
    toekomst = sorted(
        [e for e in alle_edities if e.get("sessies") and e["sessies"][0]["datum"] >= vandaag.isoformat()],
        key=lambda e: e["sessies"][0]["datum"],
    )
    for e in toekomst:
        if naam in e["deelnemers"]:
            return e, True
    for e in toekomst:
        if e["cursus_id"] in geselecteerd:
            return e, False
    for e in toekomst:
        if e["cursus_id"] in kern_cursus_ids:
            return e, False
    return None, False


def _bepaal_aanbevelingen(plan: dict, data: dict, max_items: int = 3) -> list:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    resultaat = []
    for sectie in data.get("blokken", {}).get(profiel, []):
        for item in sectie.get("items", []):
            if item.get("kern") and item["id"] not in geselecteerd:
                resultaat.append(item)
                if len(resultaat) >= max_items:
                    return resultaat
    return resultaat
```

- [ ] **Stap 5: Draai de tests — verwacht PASS**

```
pytest tests/test_home.py -v
```

Verwacht: alle 11 tests PASS.

- [ ] **Stap 6: Draai alle tests — controleer geen regressies**

```
pytest tests/ -v
```

Verwacht: alle bestaande tests nog steeds PASS.

- [ ] **Stap 7: Lint**

```
ruff check views/home.py tests/test_home.py
```

- [ ] **Stap 8: Commit**

```
git add views/home.py tests/test_home.py
git commit -m "feat: voeg home helpers toe (_bepaal_editie_kaart, _bepaal_aanbevelingen)"
```

---

## Task 3: `views/home.py` — Volledige `render()`

**Files:**
- Modify: `views/home.py` — voeg render() en hulpfuncties toe

- [ ] **Stap 1: Vervang `render()` en voeg hulpfuncties toe**

Vervang de volledige inhoud van `views/home.py` met onderstaande code (de helper-functies uit Task 2 blijven ongewijzigd, ze worden hieronder opnieuw opgenomen):

```python
# views/home.py
import streamlit as st
from datetime import date
from data.milestones import hoogste_mijlpaal
from data.sessie_utils import genereer_ics_editie, stuur_bevestigingsmail
from data.profielen import PROFIEL_KLEUREN, PROFIEL_LABELS


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    profiel = plan.get("profiel", "engineer")
    kleur = PROFIEL_KLEUREN.get(profiel, "#0072B8")
    label = PROFIEL_LABELS.get(profiel, profiel)
    geselecteerd = plan.get("geselecteerd", [])
    statussen = plan.get("statussen", {})

    cursus_lookup: dict[str, dict] = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }
    kern_cursus_ids: set[str] = {
        item["id"]
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
        if item.get("kern")
    }

    afgerond_count = sum(1 for s in statussen.values() if s == "afgerond")
    totaal = len(geselecteerd)
    pct = int(afgerond_count / totaal * 100) if totaal else 0
    huidige_fase = _bepaal_huidige_fase(plan, data)
    fase_label = f"Fase {huidige_fase['num']} — {huidige_fase['naam']}" if huidige_fase else ""

    st.markdown(
        f"""
        <div style="background:{kleur};border-radius:10px;padding:18px 20px;
                    color:#fff;margin-bottom:16px;">
          <div style="font-size:13px;opacity:.8;margin-bottom:4px;">
            Jouw voortgang · {label}
          </div>
          <div style="font-size:22px;font-weight:700;">
            {afgerond_count} van {totaal} cursussen afgerond
          </div>
          <div style="background:rgba(255,255,255,.25);border-radius:4px;
                      height:8px;margin-top:10px;">
            <div style="background:#fff;border-radius:4px;height:8px;width:{pct}%;"></div>
          </div>
          <div style="font-size:12px;opacity:.7;margin-top:6px;">
            {pct}%{"  ·  " + fase_label if fase_label else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    vandaag = date.today()
    alle_edities = gist_client.read_edities().get("edities", [])
    editie, is_ingeschreven = _bepaal_editie_kaart(
        plan, naam, alle_edities, kern_cursus_ids, vandaag
    )
    mijlpaal = hoogste_mijlpaal(plan, data)
    volgende_stap = _bepaal_volgende_stap(plan, cursus_lookup)

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("**Volgende stap**")
            if volgende_stap:
                st.markdown(
                    f"**{volgende_stap.get('icon', '')} {volgende_stap['naam']}**"
                )
                st.caption(volgende_stap.get("duur", ""))
            else:
                st.caption("Geen cursussen gepland.")

    with col2:
        if editie:
            _render_editie_kaart(
                editie, is_ingeschreven, cursus_lookup, kleur,
                naam, gist_client, plan, vandaag,
            )

    with col3:
        if mijlpaal:
            with st.container(border=True):
                st.markdown(f"**{mijlpaal.icon} Mijlpaal behaald!**")
                st.markdown(f"**{mijlpaal.label}**")

    aanbevelingen = _bepaal_aanbevelingen(plan, data)
    if aanbevelingen:
        st.divider()
        st.markdown("**💡 Aanbevolen voor jou**")
        st.caption(
            "Kern-cursussen voor jouw profiel die je nog niet hebt geselecteerd."
        )
        st.markdown(
            "  ".join(
                f"`{item.get('icon', '')} {item['naam']}`" for item in aanbevelingen
            )
        )


def _render_editie_kaart(
    editie: dict,
    is_ingeschreven: bool,
    cursus_lookup: dict,
    kleur: str,
    naam: str,
    gist_client,
    plan: dict,
    vandaag: date,
) -> None:
    cursus = cursus_lookup.get(editie["cursus_id"], {})
    cursus_naam = cursus.get("naam", editie["cursus_id"])
    eerste_sessie = editie["sessies"][0] if editie["sessies"] else {}
    datum_str = eerste_sessie.get("datum", "")
    datum_kleur = kleur if is_ingeschreven else "var(--text-muted, #888)"
    na_deadline = (
        (date.fromisoformat(datum_str) - vandaag).days < 7 if datum_str else True
    )

    with st.container(border=True):
        st.markdown("**Aankomende editie**")
        st.markdown(f"**{cursus.get('icon', '📋')} {cursus_naam}**")
        st.markdown(
            f"<div style='font-size:22px;font-weight:700;color:{datum_kleur};'>"
            f"{datum_str}</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"🕐 {eerste_sessie.get('tijd', '–')}  ·  "
            f"📍 {eerste_sessie.get('locatie', '–')}"
        )
        if is_ingeschreven:
            ics = genereer_ics_editie(editie, cursus_naam)
            st.download_button(
                "📥 Download .ics",
                data=ics,
                file_name=f"{editie['id']}.ics",
                mime="text/calendar",
                key=f"home_ics_{editie['id']}",
                use_container_width=True,
            )
            annuleer_label = (
                "Annuleren (deadline verstreken)" if na_deadline else "Afmelden"
            )
            if st.button(
                annuleer_label,
                key=f"home_annuleer_{editie['id']}",
                disabled=na_deadline,
                use_container_width=True,
            ):
                try:
                    gist_client.annuleren_editie(editie["id"], naam, vandaag)
                    st.success("Je inschrijving is geannuleerd.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            vrij = max(0, editie["max_deelnemers"] - len(editie["deelnemers"]))
            is_vol = vrij == 0
            if st.button(
                "Inschrijven" if not is_vol else "Vol",
                key=f"home_inschr_{editie['id']}",
                disabled=is_vol,
                type="primary" if not is_vol else "secondary",
                use_container_width=True,
            ):
                try:
                    gist_client.inschrijven_editie(editie["id"], naam)
                    _verstuur_bevestiging(plan, naam, editie, cursus_naam)
                    st.success("✓ Ingeschreven!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def _verstuur_bevestiging(
    plan: dict, naam: str, editie: dict, cursus_naam: str
) -> None:
    email = plan.get("email", "").strip()
    if not email:
        return
    smtp_config = {
        "host": st.secrets.get("SMTP_HOST", "smtp.office365.com"),
        "port": int(st.secrets.get("SMTP_PORT", 587)),
        "user": st.secrets["SMTP_USER"],
        "password": st.secrets["SMTP_PASSWORD"],
    }
    try:
        stuur_bevestigingsmail(naam, email, editie, cursus_naam, smtp_config)
    except Exception as e:
        st.warning(
            f"Inschrijving gelukt, maar bevestigingsmail kon niet verzonden worden. ({e})"
        )


def _bepaal_editie_kaart(
    plan: dict,
    naam: str,
    alle_edities: list,
    kern_cursus_ids: set,
    vandaag: date,
) -> tuple:
    geselecteerd = set(plan.get("geselecteerd", []))
    toekomst = sorted(
        [
            e for e in alle_edities
            if e.get("sessies") and e["sessies"][0]["datum"] >= vandaag.isoformat()
        ],
        key=lambda e: e["sessies"][0]["datum"],
    )
    for e in toekomst:
        if naam in e["deelnemers"]:
            return e, True
    for e in toekomst:
        if e["cursus_id"] in geselecteerd:
            return e, False
    for e in toekomst:
        if e["cursus_id"] in kern_cursus_ids:
            return e, False
    return None, False


def _bepaal_aanbevelingen(plan: dict, data: dict, max_items: int = 3) -> list:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    resultaat = []
    for sectie in data.get("blokken", {}).get(profiel, []):
        for item in sectie.get("items", []):
            if item.get("kern") and item["id"] not in geselecteerd:
                resultaat.append(item)
                if len(resultaat) >= max_items:
                    return resultaat
    return resultaat


def _bepaal_huidige_fase(plan: dict, data: dict):
    profiel = plan.get("profiel", "engineer")
    afgerond = {iid for iid, s in plan.get("statussen", {}).items() if s == "afgerond"}
    fases = data.get("fases", {}).get(profiel, [])
    for fase in fases:
        fase_items = set(fase.get("items", []))
        if fase_items and not fase_items.issubset(afgerond):
            return fase
    return fases[-1] if fases else None


def _bepaal_volgende_stap(plan: dict, cursus_lookup: dict):
    statussen = plan.get("statussen", {})
    for iid in plan.get("geselecteerd", []):
        if statussen.get(iid, "gepland") == "gepland":
            return cursus_lookup.get(iid)
    return None
```

- [ ] **Stap 2: Draai alle tests**

```
pytest tests/ -v
```

Verwacht: alle tests PASS (geen regressies).

- [ ] **Stap 3: Lint**

```
ruff check views/home.py
```

- [ ] **Stap 4: Commit**

```
git add views/home.py
git commit -m "feat: voeg home render() toe met voortgangsbanner, editie-kaart en aanbevelingen"
```

---

## Task 4: `app.py` — Home tab toevoegen

**Files:**
- Modify: `app.py`

- [ ] **Stap 1: Voeg Home toe als eerste tab**

Vervang in `app.py` de tabs-definitie en de tab-blokken. Wijzig:

```python
    # Oud — 8 tabs
    tabs = st.tabs([
        "◈ Bouwblokken",
        "→ Roadmap",
        ...
    ])

    with tabs[0]:
        from views.bouwblokken import render as render_bouwblokken
        render_bouwblokken(data, plan, client, naam)
    ...
```

Naar (Home als tabs[0], bestaande tabs schuiven één op):

```python
    tabs = st.tabs([
        "🏠 Home",
        "◈ Bouwblokken",
        "→ Roadmap",
        "◉ Skill Map",
        "★ Mijn Plan",
        "≡ Alle cursussen",
        "⏱ Tijdlijn",
        "📅 Kalender",
        "⚙️ Beheer",
    ])

    with tabs[0]:
        from views.home import render as render_home
        render_home(data, plan, client, naam)

    with tabs[1]:
        from views.bouwblokken import render as render_bouwblokken
        render_bouwblokken(data, plan, client, naam)

    with tabs[2]:
        from views.roadmap import render as render_roadmap
        render_roadmap(data, plan)

    with tabs[3]:
        from views.skillmap import render as render_skillmap
        render_skillmap(data, plan)

    with tabs[4]:
        from views.mijn_plan import render as render_plan
        render_plan(data, plan, client, naam)

    with tabs[5]:
        from views.alle_cursussen import render as render_overzicht
        render_overzicht(data, plan)

    with tabs[6]:
        from views.tijdlijn import render as render_tijdlijn
        render_tijdlijn(data, plan)

    with tabs[7]:
        from views.kalender import render as render_kalender
        render_kalender(data, plan, client, naam)

    with tabs[8]:
        from views.beheer import render as render_beheer
        render_beheer(data, client)
```

- [ ] **Stap 2: Draai alle tests**

```
pytest tests/ -v
```

Verwacht: alle tests PASS.

- [ ] **Stap 3: Lint**

```
ruff check app.py
```

- [ ] **Stap 4: Commit**

```
git add app.py
git commit -m "feat: voeg Home toe als eerste tab in app.py"
```

---

## Task 5: `views/mijn_plan.py` — Toast bij mijlpaal

**Files:**
- Modify: `views/mijn_plan.py`

- [ ] **Stap 1: Voeg import toe bovenaan `views/mijn_plan.py`**

Voeg toe na de bestaande imports (regel 1-3):

```python
from data.milestones import bereken_mijlpalen
```

- [ ] **Stap 2: Pas het `if wijziging:` blok aan**

Huidige code in `render()`:

```python
    if wijziging:
        plan["statussen"] = statussen
        plan["laatst_actief"] = str(date.today())
        st.session_state["plan"] = plan
        gist_client.save_plan(naam, plan)
        st.rerun()
```

Vervang door:

```python
    if wijziging:
        mijlpalen_voor_ids = {m.id for m in bereken_mijlpalen(plan, data)}
        plan["statussen"] = statussen
        plan["laatst_actief"] = str(date.today())
        st.session_state["plan"] = plan
        gist_client.save_plan(naam, plan)
        nieuwe_mijlpalen = [
            m for m in bereken_mijlpalen(plan, data)
            if m.id not in mijlpalen_voor_ids
        ]
        for m in nieuwe_mijlpalen:
            st.toast(f"{m.icon} {m.label}!", icon="🎉")
        st.rerun()
```

Let op: `mijlpalen_voor_ids` wordt berekend **vóór** `plan["statussen"] = statussen`. Omdat `statussen` dezelfde dict-referentie is als `plan["statussen"]` (Python muteert in-place via `statussen[iid] = nieuwe_status` in de loop), is dit equivalent aan berekenen vóór enige statuswijziging. De mijlpalen ná de update worden berekend op de al-gemuteerde `plan`.

- [ ] **Stap 3: Draai alle tests**

```
pytest tests/ -v
```

Verwacht: alle tests PASS.

- [ ] **Stap 4: Lint**

```
ruff check views/mijn_plan.py
```

- [ ] **Stap 5: Commit**

```
git add views/mijn_plan.py
git commit -m "feat: toon toast-notificatie bij nieuw behaalde mijlpaal in Mijn Plan"
```

---

## Spec-dekking self-review

| Spec §  | Gedekt door |
|---|---|
| §1 Thuisscherm — voortgangsbanner | Task 3 (`render()`) |
| §1 Thuisscherm — 3-koloms kaartgrid | Task 3 (`render()`) |
| §1.1 Editie-prioriteitslogica | Task 2 (`_bepaal_editie_kaart`) |
| §1 Home als eerste tab | Task 4 (`app.py`) |
| §2 Toast bij mijlpaal | Task 5 (`mijn_plan.py`) |
| §2 Permanente mijlpaalkaart | Task 3 (`render()`) |
| §2 Mijlpaalberekening | Task 1 (`milestones.py`) |
| §3 Aanbevelingen | Task 2 (`_bepaal_aanbevelingen`) + Task 3 |
| §4 Optimistische updates plan | Task 5 (toast vóór rerun; plan-update was al aanwezig) |
