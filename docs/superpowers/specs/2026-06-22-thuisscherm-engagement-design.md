# Design: Thuisscherm + Engagement (Aanpak 1 — Launch-ready)

**Datum:** 2026-06-22  
**Status:** Goedgekeurd  
**Context:** De app wordt binnenkort gecommuniceerd naar alle KZA-collega's. Dit ontwerp bereidt de app voor op die uitrol met een persoonlijk thuisscherm, voortgang-viering en basisaanbevelingen.

---

## Scope

Drie onderdelen:

1. **Thuisscherm** — nieuw dashboard als eerste tab (`views/home.py`)
2. **Voortgang vieren** — mijlpalen via toast + permanente kaart
3. **Aanbevelingen** — rule-based, geen ML

Buiten scope: sociale laag (pas zinvol bij meer gebruikers, voorbereid in data-laag), Gist vervangen, edities-caching (eerder bewust verwijderd wegens multi-user stale data).

---

## 1. Thuisscherm

### Positie
Nieuwe tab `🏠 Home` wordt de **eerste tab** in `app.py`. De huidige tabs blijven ongewijzigd.

### Indeling (top → bottom)

**Voortgangsbanner**
- Brede banner met profielkleur als achtergrond
- Toont: naam, profiel-label, `X van Y cursussen afgerond`, progressiebalk, huidige fase

**3-koloms kaartgrid**

| Kaart | Inhoud | Wanneer zichtbaar |
|---|---|---|
| Volgende stap | Eerste item in huidige fase met status "gepland" | Als er een gepland item is |
| Aankomende editie | Zie §1.1 | Als er een relevante editie is |
| Mijlpaal | Hoogste behaalde mijlpaal (zie §2) | Als er een mijlpaal is behaald |

**Aanbevolen voor jou**
- Chip-rij met aanbevolen cursussen (zie §3)
- Alleen zichtbaar als er aanbevelingen zijn

### 1.1 Aankomende editie — prioriteitslogica

De editiekaart toont de eerstvolgende relevante editie op basis van deze volgorde:

1. **Ingeschreven** — editie waar `naam in editie["deelnemers"]`; datum groot en in profielkleur weergegeven; acties: `.ics` downloaden, afmelden
2. **Op leerplan** — editie waarvan `cursus_id in plan["geselecteerd"]`, nog niet ingeschreven; datum in neutrale kleur; actie: inschrijven-knop
3. **Kern-cursus van profiel** — editie van een kern-cursus voor het profiel die nog niet geselecteerd is; zelfde weergave als 2

Als er niets relevants is, wordt de kaart niet getoond.

### Implementatie
- Nieuw bestand `views/home.py`, `render(data, plan, gist_client, naam)` — zelfde signature als andere views
- Helperfunctie `_bepaal_editie_kaart(plan, naam, alle_edities, cursus_lookup, profiel_cursus_ids, vandaag: date)` → `(editie | None, is_ingeschreven: bool)`; filtert op toekomstige edities (`eerste_datum >= vandaag`)
- `app.py`: Home als eerste tab toevoegen, lazy import zoals de andere tabs

---

## 2. Voortgang vieren — mijlpalen

### Weergave
- **Toast** (`st.toast`) op het moment dat een mijlpaal wordt bereikt (bij het opslaan van een statuswijziging in `views/mijn_plan.py`)
- **Permanente kaart** op het thuisscherm: toont de hoogste behaalde mijlpaal (geordend: eerste cursus → fase N voltooid → alle kern → leerplan volledig)

### Mijlpalen (berekend on-the-fly, geen extra databaseveld)

| Mijlpaal | Conditie |
|---|---|
| Eerste cursus afgerond | `len([s for s in statussen.values() if s == "afgerond"]) == 1` |
| Fase N voltooid | Alle items in fase N hebben status "afgerond" |
| Alle kern-cursussen afgerond | Alle `kern=True` items voor het profiel zijn afgerond |
| Leerplan volledig | Alle items in `plan["geselecteerd"]` hebben status "afgerond" |

### Implementatie
- Nieuwe module `data/milestones.py` met `bereken_mijlpalen(plan, data) -> list[Mijlpaal]` en `hoogste_mijlpaal(plan, data) -> Mijlpaal | None`
- `views/mijn_plan.py`: na elke statuswijziging `bereken_mijlpalen` aanroepen en bij nieuwe mijlpaal `st.toast` tonen
- `views/home.py`: `hoogste_mijlpaal` aanroepen voor de mijlpaalkaart

---

## 3. Aanbevelingen

### Logica (rule-based, in volgorde van prioriteit)

1. **Volgende stap** — eerste item in huidige fase met status `"gepland"` (al in de Volgende stap-kaart, geen aparte chip)
2. **Kern-cursussen niet geselecteerd** — `kern=True` items voor het profiel die niet in `plan["geselecteerd"]` zitten; max. 3 chips
3. **Populair bij profielgenoten** *(fase 2, nog niet implementeren)* — cursussen die medewerkers met hetzelfde profiel vaak selecteren; pas zinvol bij ≥10 gebruikers

### Implementatie
- Helperfunctie `_bepaal_aanbevelingen(plan, data, max=3) -> list[CursusItem]` in `views/home.py`
- Weergave: chip-rij (`st.markdown` of kleine containers); niet klikbaar (Streamlit ondersteunt geen programmatische tabwissel)

---

## 4. Performance — optimistische updates

Edities-caching wordt **niet** opnieuw ingevoerd (eerder verwijderd wegens multi-user stale data, commit `16aa744`).

Wél: na een schrijfactie wordt `st.session_state` direct bijgewerkt zodat de UI van de huidige gebruiker meteen klopt zonder te wachten op de volgende Gist-read.

- **Schrijfacties via `gist_client`** (`save_plan`, `inschrijven_editie`, `annuleren_editie`) retourneren het bijgewerkte object; views slaan dit op in `session_state`
- Van toepassing op: statuswijzigingen in `mijn_plan.py`, inschrijven/afmelden in `kalender.py` en `home.py`

---

## Datamodel — geen wijzigingen

Het bestaande datamodel (`cursussen.json`, `plannen.json`, `sessies.json`) is ongewijzigd. Mijlpalen worden berekend uit bestaande velden in `plan.statussen` en `data.blokken/fases` — er hoeft niets extra te worden opgeslagen.

---

## Testscope

- `tests/test_milestones.py` — unit tests voor alle mijlpaalcondities
- `tests/test_home.py` — test voor `_bepaal_editie_kaart` (prioriteitslogica) en `_bepaal_aanbevelingen`
- Bestaande tests ongewijzigd
