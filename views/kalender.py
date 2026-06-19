# views/kalender.py
import streamlit as st
from datetime import date
from data.sessie_utils import genereer_ics, stuur_bevestigingsmail

PROFIEL_LABELS = {
    "engineer": "QA Engineer",
    "enabler":  "QA Enabler",
    "academy":  "KZAcademy",
    "maatwerk": "Op maat",
    "security": "Security",
    "ai":       "AI",
}


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    st.markdown("### 📅 Cursuskalender")
    st.caption("Geplande sessies. Schrijf je in en download een agenda-uitnodiging (.ics).")

    sessies_data = gist_client.read_sessies()
    alle_sessies = sessies_data.get("sessies", [])

    if not alle_sessies:
        st.info("Er zijn nog geen sessies ingepland. Vraag een beheerder om sessies toe te voegen.")
        return

    # Bouw cursus-lookup: id → {naam, icon}
    cursus_lookup: dict[str, dict] = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    # Bouw profiel → set van cursus_ids
    profiel_cursus_ids: dict[str, set] = {
        profiel: {
            item["id"]
            for sectie in secties
            for item in sectie.get("items", [])
        }
        for profiel, secties in data.get("blokken", {}).items()
    }

    # Filter bovenaan
    profielen = list(data.get("profielen", {}).keys())
    mijn_profiel = plan.get("profiel", profielen[0] if profielen else "engineer")
    ALLE = "Alle profielen"
    profiel_opties = [ALLE] + profielen
    default_index = profiel_opties.index(mijn_profiel) if mijn_profiel in profiel_opties else 0
    filter_profiel = st.radio(
        "Filter op profiel",
        profiel_opties,
        index=default_index,
        format_func=lambda k: k if k == ALLE else PROFIEL_LABELS.get(k, k),
        horizontal=True,
        label_visibility="collapsed",
    )

    # Sorteer en filter
    vandaag = date.today()
    sessies = sorted(
        [s for s in alle_sessies if date.fromisoformat(s["datum"]) >= vandaag],
        key=lambda s: s["datum"],
    )
    if filter_profiel != ALLE:
        cursus_ids_voor_profiel = profiel_cursus_ids.get(filter_profiel, set())
        sessies = [s for s in sessies if s["cursus_id"] in cursus_ids_voor_profiel]

    if not sessies:
        st.info("Geen aankomende sessies voor dit profiel.")
        return

    mijn_inschrijvingen = {s["id"] for s in gist_client.get_sessies_voor_medewerker(naam)}

    for sessie in sessies:
        cursus = cursus_lookup.get(sessie["cursus_id"], {})
        cursus_naam = f"{cursus.get('icon', '📋')} {cursus.get('naam', sessie['cursus_id'])}"
        bezet = len(sessie["deelnemers"])
        max_d = sessie["max_deelnemers"]
        vrij = max(0, max_d - bezet)
        is_vol = vrij == 0
        is_ingeschreven = sessie["id"] in mijn_inschrijvingen
        sessiedatum = date.fromisoformat(sessie["datum"])
        na_deadline = (sessiedatum - vandaag).days < 7

        with st.container(border=True):
            col_info, col_acties = st.columns([3, 2])

            with col_info:
                st.markdown(f"**{cursus_naam}**")
                st.caption(
                    f"📅 {sessie['datum']}  ·  "
                    f"🕐 {sessie.get('tijd', '–')}  ·  "
                    f"📍 {sessie.get('locatie', '–')}"
                )
                if is_vol:
                    st.markdown("🔴 **Vol**")
                else:
                    st.markdown(f"🟢 **{vrij} van {max_d} plekken vrij**")

            with col_acties:
                if is_ingeschreven:
                    st.success("✓ Ingeschreven")

                    ics_inhoud = genereer_ics(sessie, cursus.get("naam", sessie["cursus_id"]))
                    st.download_button(
                        "📥 Download .ics",
                        data=ics_inhoud,
                        file_name=f"{sessie['id']}.ics",
                        mime="text/calendar",
                        key=f"ics_{sessie['id']}",
                        use_container_width=True,
                    )

                    annuleer_label = "Annuleren (deadline verstreken)" if na_deadline else "Afmelden"
                    if st.button(
                        annuleer_label,
                        key=f"annuleer_{sessie['id']}",
                        disabled=na_deadline,
                        use_container_width=True,
                    ):
                        try:
                            gist_client.annuleren(sessie["id"], naam, vandaag)
                            st.success("Je inschrijving is geannuleerd.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                else:
                    if st.button(
                        "Inschrijven" if not is_vol else "Vol",
                        key=f"inschr_{sessie['id']}",
                        disabled=is_vol,
                        type="primary" if not is_vol else "secondary",
                        use_container_width=True,
                    ):
                        try:
                            gist_client.inschrijven(sessie["id"], naam)
                            _verstuur_bevestiging(plan, naam, sessie, cursus.get("naam", sessie["cursus_id"]))
                            st.success("✓ Ingeschreven! Download hieronder je agenda-uitnodiging.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))


def _verstuur_bevestiging(plan: dict, naam: str, sessie: dict, cursus_naam: str) -> None:
    email = plan.get("email", "").strip()
    if not email:
        return
    try:
        smtp_config = {
            "host": st.secrets.get("SMTP_HOST", "smtp.office365.com"),
            "port": int(st.secrets.get("SMTP_PORT", 587)),
            "user": st.secrets["SMTP_USER"],
            "password": st.secrets["SMTP_PASSWORD"],
        }
        stuur_bevestigingsmail(naam, email, sessie, cursus_naam, smtp_config)
    except Exception:
        pass
