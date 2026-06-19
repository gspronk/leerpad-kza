# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
streamlit run app.py

# Tests
pytest tests/ -v
pytest tests/test_edities.py::test_inschrijven_editie_voegt_naam_toe  # single test

# Lint (CI uses this; must be clean before merging)
ruff check .
ruff check . --fix  # auto-fix
```

CI runs on push to `main` and `feature/**` branches: lint (`ruff`) + tests (`pytest`).

## Architecture

**GitHub Gist is the database.** There is no SQL database or backend server. All persistent state lives in three JSON files in a single GitHub Gist, accessed via PyGithub:

| File | Contents |
|---|---|
| `cursussen.json` | Course catalogue (timeless: profiles, sections, items, phases) |
| `plannen.json` | Per-medewerker learning plan and progress |
| `sessies.json` | Planned edities with enrollments |

`data/gist.py` — `GistClient` is the only class that touches the Gist. It has a TTL cache (5 min) for `cursussen` and `plannen`. Sessies/edities are always fetched fresh (no cache) because enrollment state must be current.

**Streamlit single-page app.** `app.py` owns the login gate and the 8-tab layout. Each tab does a lazy import of its view module. Views receive `data` (cursussen), `plan` (medewerker plan), `gist_client`, and `naam` and are responsible for their own UI and write operations.

**View modules** in `views/`:
- `bouwblokken.py` — course catalogue per profile
- `roadmap.py`, `skillmap.py`, `tijdlijn.py` — visualisations
- `mijn_plan.py` — personal course selection and status
- `alle_cursussen.py` — full catalogue list
- `kalender.py` — upcoming edities with enrollment
- `beheer.py` — admin: manage courses, phases, and edities

**Component:** `components/sidebar.py` handles login (URL param `?naam=`, session_state, or new profile form) and returns `(naam, profiel, plan)`.

## Domain vocabulary (use these terms exactly)

- **Cursus** — a course item in the catalogue (not: training, module, les)
- **Profiel** — one of six learning tracks: engineer, enabler, academy, maatwerk, security, ai
- **Fase** — an ordered step within a Profiel
- **Editie** — a scheduled run of a Cursus, consisting of one or more Sessies; the unit you enroll in
- **Sessie** — a single meeting within an Editie (date, time, location)
- **Medewerker** — a KZA employee using the app (not: gebruiker, cursist)
- **Leerplan** — a Medewerker's personal course selection and statuses
- **Inschrijving** — the enrollment link between Medewerker and Editie
- **Annulering** — cancellation of an Inschrijving; only allowed > 7 days before the first Sessie

## Key data structures

```json
// sessies.json — note: key is "edities", not "sessies"
{
  "edities": [
    {
      "id": "edit-selenium-advanced-202603",
      "cursus_id": "selenium-advanced",
      "naam": "Editie maart 2026",
      "max_deelnemers": 12,
      "deelnemers": ["Gerson", "Anna"],
      "sessies": [
        { "datum": "2026-03-03", "tijd": "09:00", "locatie": "KZA kantoor" },
        { "datum": "2026-03-04", "tijd": "09:00", "locatie": "Klantlocatie Utrecht" }
      ]
    }
  ]
}
```

Enrollment is stored on the Editie (`deelnemers[]`), not on individual Sessies.
Deletion is blocked when 5 or more Medewerkers are enrolled (`MAX_DEELNEMERS_VERWIJDER_LIMIET = 4` in `views/beheer.py`).

## Secrets

The app requires `.streamlit/secrets.toml` with:
```toml
GITHUB_TOKEN = "..."
GIST_ID = "..."
PASSWORD = "..."
APP_URL = "http://localhost:8501"
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USER = "..."
SMTP_PASSWORD = "..."
```

## Workflow for new features

Follow `/grill-with-docs` (requirements + ADR) → `/tdd` (implementation). ADRs live in `docs/adr/`.
