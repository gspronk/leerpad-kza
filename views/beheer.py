# views/beheer.py
import streamlit as st

PROFIELEN = ["engineer", "enabler", "academy", "maatwerk", "security", "ai"]
PROFIEL_LABELS = {
    "engineer": "QA Engineer",
    "enabler":  "QA Enabler",
    "academy":  "KZAcademy",
    "maatwerk": "Op maat",
    "security": "Security",
    "ai":       "AI",
}

# Profielen waarvoor fase-beheer beschikbaar is (items-gebaseerd)
FASES_PROFIELEN = ["engineer", "enabler", "academy", "maatwerk", "security", "ai"]


def render(data: dict, gist_client) -> None:
    st.markdown("### ⚙️ Catalogus beheren")
    st.caption("Wijzigingen worden direct opgeslagen naar GitHub Gist. Alle gebruikers zien de nieuwe catalogus na een refresh.")

    tab_cursussen, tab_fases, tab_sessies = st.tabs(["📋 Cursussen", "📍 Fases", "📅 Sessies"])

    with tab_fases:
        _render_fases_beheer(data, gist_client)

    with tab_sessies:
        _render_sessies_beheer(data, gist_client)

    with tab_cursussen:
        col_zoek, col_filter = st.columns([2, 1])
        with col_zoek:
            zoek = st.text_input("Zoek cursus", placeholder="naam of id...")
        with col_filter:
            filter_profiel = st.selectbox(
                "Profiel", ["Alle"] + PROFIELEN,
                format_func=lambda k: "Alle profielen" if k == "Alle" else PROFIEL_LABELS[k]
            )

        alle_items = []
        for profiel, secties in data.get("blokken", {}).items():
            for sectie in secties:
                for item in sectie.get("items", []):
                    alle_items.append({
                        **item,
                        "_profiel": profiel,
                        "_sectie": sectie["sectie"],
                        "_badge": sectie.get("badge", "")
                    })

        gefilterd = [
            i for i in alle_items
            if (filter_profiel == "Alle" or i["_profiel"] == filter_profiel)
            and (not zoek or zoek.lower() in i["naam"].lower() or zoek.lower() in i["id"])
        ]

        st.caption(f"{len(gefilterd)} cursussen")

        if "beheer_actief_id" not in st.session_state:
            st.session_state["beheer_actief_id"] = None
        if "beheer_nieuw" not in st.session_state:
            st.session_state["beheer_nieuw"] = False

        col_lijst, col_form = st.columns([1, 2])

        with col_lijst:
            if st.button("+ Nieuwe cursus", use_container_width=True, type="primary"):
                st.session_state["beheer_nieuw"] = True
                st.session_state["beheer_actief_id"] = None

            for item in gefilterd:
                actief = st.session_state["beheer_actief_id"] == item["id"]
                label = f"{'▶ ' if actief else ''}{item.get('icon','')} {item['naam']}"
                if st.button(label, key=f"beheer_sel_{item['id']}", use_container_width=True):
                    st.session_state["beheer_actief_id"] = item["id"]
                    st.session_state["beheer_nieuw"] = False
                    st.rerun()

        with col_form:
            if st.session_state["beheer_nieuw"]:
                _render_nieuw_formulier(data, gist_client)
            elif st.session_state["beheer_actief_id"]:
                actief_item = next(
                    (i for i in alle_items if i["id"] == st.session_state["beheer_actief_id"]), None
                )
                if actief_item:
                    _render_bewerk_formulier(actief_item, data, gist_client)
            else:
                st.info("Selecteer een cursus om te bewerken, of voeg een nieuwe toe.")


def _render_fases_beheer(data: dict, gist_client) -> None:
    st.markdown("#### Fases per profiel")
    st.caption("Koppel cursussen aan een fase. De volgorde in de roadmap volgt de fase-nummering.")

    # Profielkeuze (alleen profielen met items-gebaseerde fases)
    profiel = st.selectbox(
        "Profiel",
        FASES_PROFIELEN,
        format_func=lambda k: PROFIEL_LABELS[k],
        key="fases_profiel_select"
    )

    fases = data.get("fases", {}).get(profiel, [])
    if not fases:
        st.info(f"Geen fases gedefinieerd voor {PROFIEL_LABELS[profiel]}.")
        return

    # Alle cursus-IDs voor dit profiel
    alle_profiel_ids = {
        item["id"]: item
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
    }

    # Globale lookup voor naam-weergave van cross-linked cursussen
    alle_ids_global = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    # IDs die al in een fase zitten
    ids_in_fase = {iid for fase in fases for iid in fase.get("items", [])}

    # Niet-gekoppelde cursussen
    ontkoppeld = [item for iid, item in alle_profiel_ids.items() if iid not in ids_in_fase]

    wijziging = False

    for fase in fases:
        fase_items = fase.get("items", [])
        st.markdown(f"---\n**Fase {fase['num']} — {fase.get('naam', '')}**")
        st.caption(fase.get("desc", ""))

        # Toon gekoppelde cursussen met verwijderknop
        if fase_items:
            for iid in list(fase_items):
                item = alle_profiel_ids.get(iid) or alle_ids_global.get(iid)
                naam_label = f"{item.get('icon','')} {item['naam']}" if item else iid
                col_naam, col_btn = st.columns([6, 1])
                col_naam.markdown(f"<span style='font-size:13px'>{naam_label}</span>", unsafe_allow_html=True)
                if col_btn.button("✕", key=f"fase_rm_{fase['num']}_{iid}", help="Verwijder uit fase"):
                    fase_items.remove(iid)
                    wijziging = True
        else:
            st.caption("*Nog geen cursussen gekoppeld.*")

        # Voeg cursus toe aan deze fase
        beschikbaar = [item for item in ontkoppeld if item["id"] not in fase_items]
        if beschikbaar:
            opties = {f"{i.get('icon','')} {i['naam']}": i["id"] for i in beschikbaar}
            col_sel, col_add = st.columns([5, 1])
            keuze = col_sel.selectbox(
                "Cursus toevoegen",
                ["— kies —"] + list(opties.keys()),
                key=f"fase_add_sel_{fase['num']}",
                label_visibility="collapsed"
            )
            if col_add.button("＋", key=f"fase_add_btn_{fase['num']}", help="Toevoegen aan fase"):
                if keuze != "— kies —":
                    toe_te_voegen = opties[keuze]
                    fase_items.append(toe_te_voegen)
                    # Verwijder uit ontkoppeld zodat je hem niet dubbel kunt toevoegen
                    ontkoppeld = [i for i in ontkoppeld if i["id"] != toe_te_voegen]
                    wijziging = True

    if ontkoppeld:
        st.markdown("---")
        st.caption(f"**{len(ontkoppeld)} cursussen niet gekoppeld aan een fase:** " +
                   ", ".join(f"{i.get('icon','')} {i['naam']}" for i in ontkoppeld))

    if wijziging:
        gist_client.write_cursussen(data)
        st.success("✓ Fases opgeslagen.")
        st.rerun()


def _render_nieuw_formulier(data: dict, gist_client) -> None:
    st.markdown("#### Nieuwe cursus")
    with st.form("nieuw_cursus_form"):
        nieuw_id  = st.text_input("ID (uniek, geen spaties)", placeholder="bijv. sec-pentest-2")
        naam      = st.text_input("Naam")
        icon      = st.text_input("Icoon (emoji)", value="📋")
        desc      = st.text_area("Beschrijving", height=80)
        profiel   = st.selectbox("Profiel", PROFIELEN, format_func=lambda k: PROFIEL_LABELS[k])
        sectie    = st.text_input("Sectie", placeholder="bijv. Security")
        badge     = st.text_input("Badge", placeholder="bijv. Specialisatie")
        duur      = st.text_input("Duur", placeholder="bijv. 2 sessies")
        kern      = st.checkbox("Essentieel")
        cross_str = st.text_input("Cross-functioneel (komma-gescheiden)", placeholder="bijv. enabler, maatwerk")
        tags_str  = st.text_input("Tags (komma-gescheiden)", placeholder="bijv. Security, OWASP")
        opgeslagen = st.form_submit_button("✓ Opslaan", use_container_width=True)

    if opgeslagen:
        if not nieuw_id.strip() or not naam.strip():
            st.error("ID en naam zijn verplicht.")
            return
        alle_ids = {
            i["id"]
            for secties in data.get("blokken", {}).values()
            for sec in secties
            for i in sec.get("items", [])
        }
        if nieuw_id.strip() in alle_ids:
            st.error(f"ID '{nieuw_id.strip()}' bestaat al.")
            return

        nieuw_item = {
            "id":    nieuw_id.strip(),
            "naam":  naam.strip(),
            "icon":  icon.strip(),
            "desc":  desc.strip(),
            "tags":  [t.strip() for t in tags_str.split(",") if t.strip()],
            "duur":  duur.strip(),
            "kern":  kern,
            "cross": [c.strip() for c in cross_str.split(",") if c.strip()],
        }

        blokken = data.get("blokken", {})
        prof_blokken = blokken.setdefault(profiel, [])
        sectie_match = next((s for s in prof_blokken if s["sectie"] == sectie.strip()), None)
        if sectie_match:
            sectie_match["items"].append(nieuw_item)
        else:
            prof_blokken.append({"sectie": sectie.strip(), "badge": badge.strip(), "items": [nieuw_item]})

        gist_client.write_cursussen(data)
        st.success(f"✓ '{naam}' toegevoegd en opgeslagen.")
        st.session_state["beheer_nieuw"] = False
        st.rerun()


def _render_bewerk_formulier(item: dict, data: dict, gist_client) -> None:
    st.markdown(f"#### Bewerk: {item.get('icon','')} {item['naam']}")
    huidig_profiel = item.get("_profiel", "engineer")
    huidig_sectie  = item.get("_sectie", "")

    with st.form(f"bewerk_form_{item['id']}"):
        naam      = st.text_input("Naam",        value=item.get("naam", ""))
        icon      = st.text_input("Icoon",       value=item.get("icon", ""))
        desc      = st.text_area("Beschrijving", value=item.get("desc", ""), height=80)
        duur      = st.text_input("Duur",        value=item.get("duur", ""))
        kern      = st.checkbox("Essentieel",    value=item.get("kern", False))
        cross_str = st.text_input("Cross-functioneel", value=", ".join(item.get("cross", [])))
        tags_str  = st.text_input("Tags",        value=", ".join(item.get("tags", [])))

        st.markdown("---")
        nieuw_profiel = st.selectbox(
            "Profiel",
            PROFIELEN,
            index=PROFIELEN.index(huidig_profiel) if huidig_profiel in PROFIELEN else 0,
            format_func=lambda k: PROFIEL_LABELS[k],
        )
        nieuw_sectie = st.text_input("Sectie", value=huidig_sectie)

        col1, col2 = st.columns(2)
        opgeslagen  = col1.form_submit_button("✓ Opslaan",     use_container_width=True)
        verwijderen = col2.form_submit_button("🗑 Verwijderen", use_container_width=True)

    if opgeslagen:
        updates = {
            "naam":  naam.strip(),
            "icon":  icon.strip(),
            "desc":  desc.strip(),
            "duur":  duur.strip(),
            "kern":  kern,
            "cross": [c.strip() for c in cross_str.split(",") if c.strip()],
            "tags":  [t.strip() for t in tags_str.split(",") if t.strip()],
        }
        if nieuw_profiel != huidig_profiel or nieuw_sectie.strip() != huidig_sectie:
            # Verplaats naar nieuw profiel / sectie
            _verwijder_item_uit_data(data, item["id"])
            nieuw_item = {**item, **updates}
            # Verwijder interne velden
            for k in ["_profiel", "_sectie", "_badge"]:
                nieuw_item.pop(k, None)
            blokken = data.get("blokken", {})
            prof_blokken = blokken.setdefault(nieuw_profiel, [])
            sectie_match = next((s for s in prof_blokken if s["sectie"] == nieuw_sectie.strip()), None)
            if sectie_match:
                sectie_match["items"].append(nieuw_item)
            else:
                prof_blokken.append({"sectie": nieuw_sectie.strip(), "badge": "", "items": [nieuw_item]})
        else:
            _update_item_in_data(data, item["id"], updates)

        gist_client.write_cursussen(data)
        st.success("✓ Opgeslagen.")
        st.session_state["beheer_actief_id"] = None
        st.rerun()

    if verwijderen:
        _verwijder_item_uit_data(data, item["id"])
        gist_client.write_cursussen(data)
        st.success(f"🗑 '{item['naam']}' verwijderd.")
        st.session_state["beheer_actief_id"] = None
        st.rerun()


def _update_item_in_data(data: dict, item_id: str, updates: dict) -> None:
    for secties in data.get("blokken", {}).values():
        for sectie in secties:
            for item in sectie.get("items", []):
                if item["id"] == item_id:
                    item.update(updates)
                    return


def _verwijder_item_uit_data(data: dict, item_id: str) -> None:
    for secties in data.get("blokken", {}).values():
        for sectie in secties:
            sectie["items"] = [i for i in sectie.get("items", []) if i["id"] != item_id]


def _render_sessies_beheer(data: dict, gist_client) -> None:
    import streamlit as st
    from datetime import date

    st.markdown("#### Sessiebeheer")
    st.caption("Voeg geplande uitvoeringen toe per cursus. Deelnemers kunnen zich inschrijven via de Kalender-tab.")

    sessies_data = gist_client.read_sessies()
    alle_sessies = sessies_data.get("sessies", [])

    cursus_lookup: dict[str, dict] = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    # Groepeer sessies per cursus
    sessies_per_cursus: dict[str, list] = {}
    for sessie in alle_sessies:
        sessies_per_cursus.setdefault(sessie["cursus_id"], []).append(sessie)

    # Nieuwe sessie toevoegen
    st.markdown("##### Nieuwe sessie toevoegen")
    with st.form("nieuwe_sessie_form"):
        cursus_opties = {
            f"{c.get('icon', '📋')} {c['naam']} ({cid})": cid
            for cid, c in sorted(cursus_lookup.items(), key=lambda x: x[1].get("naam", ""))
        }
        cursus_keuze = st.selectbox("Cursus", list(cursus_opties.keys()))
        col1, col2 = st.columns(2)
        datum = col1.date_input("Datum", min_value=date.today())
        tijd = col2.text_input("Tijd", value="09:00", placeholder="09:00")
        locatie = st.text_input("Locatie", placeholder="KZA kantoor")
        max_d = st.number_input("Max. deelnemers", min_value=1, max_value=100, value=12)
        opgeslagen = st.form_submit_button("＋ Sessie toevoegen", use_container_width=True)

    if opgeslagen and cursus_keuze:
        cursus_id = cursus_opties[cursus_keuze]
        datum_str = datum.strftime("%Y-%m-%d")
        sessie_id = f"sess-{cursus_id}-{datum_str.replace('-', '')}"
        if any(s["id"] == sessie_id for s in alle_sessies):
            st.error("Er bestaat al een sessie voor deze cursus op die datum.")
        else:
            alle_sessies.append({
                "id": sessie_id,
                "cursus_id": cursus_id,
                "datum": datum_str,
                "tijd": tijd.strip(),
                "locatie": locatie.strip(),
                "max_deelnemers": int(max_d),
                "deelnemers": [],
            })
            gist_client.write_sessies({"sessies": alle_sessies})
            st.success(f"✓ Sessie toegevoegd voor {datum_str}.")
            st.rerun()

    # Overzicht bestaande sessies
    if not alle_sessies:
        st.info("Nog geen sessies aangemaakt.")
        return

    st.markdown("##### Bestaande sessies")
    sessies_gesorteerd = sorted(alle_sessies, key=lambda s: s["datum"])
    for sessie in sessies_gesorteerd:
        cursus = cursus_lookup.get(sessie["cursus_id"], {})
        cursus_naam = f"{cursus.get('icon', '📋')} {cursus.get('naam', sessie['cursus_id'])}"
        bezet = len(sessie["deelnemers"])
        max_d = sessie["max_deelnemers"]

        with st.expander(f"{cursus_naam} — {sessie['datum']} ({bezet}/{max_d} ingeschreven)"):
            st.caption(f"ID: `{sessie['id']}` · Locatie: {sessie.get('locatie', '–')} · Tijd: {sessie.get('tijd', '–')}")
            if sessie["deelnemers"]:
                st.markdown("**Ingeschreven:** " + ", ".join(sessie["deelnemers"]))
            else:
                st.caption("Nog geen inschrijvingen.")

            if bezet == 0:
                if st.button("🗑 Sessie verwijderen", key=f"del_sess_{sessie['id']}"):
                    sessies_data["sessies"] = [s for s in alle_sessies if s["id"] != sessie["id"]]
                    gist_client.write_sessies(sessies_data)
                    st.success("Sessie verwijderd.")
                    st.rerun()
            else:
                st.caption("⚠️ Sessie kan niet worden verwijderd zolang er inschrijvingen zijn.")
