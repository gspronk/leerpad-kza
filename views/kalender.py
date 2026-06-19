# views/kalender.py
import streamlit as st
from datetime import date
from data.sessie_utils import genereer_ics_editie, stuur_bevestigingsmail

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
    st.caption("Geplande edities. Schrijf je in en download een agenda-uitnodiging (.ics).")

    edities_data = gist_client.read_edities()
    alle_edities = edities_data.get("edities", [])

    if not alle_edities:
        st.info("Er zijn nog geen edities ingepland. Vraag een beheerder om edities toe te voegen.")
        return

    cursus_lookup: dict[str, dict] = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    profiel_cursus_ids: dict[str, set] = {
        profiel: {
            item["id"]
            for sectie in secties
            for item in sectie.get("items", [])
        }
        for profiel, secties in data.get("blokken", {}).items()
    }

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

    vandaag = date.today()

    def eerste_datum(editie):
        return editie["sessies"][0]["datum"] if editie["sessies"] else "9999-99-99"

    edities = sorted(
        [e for e in alle_edities if eerste_datum(e) >= vandaag.isoformat()],
        key=eerste_datum,
    )
    if filter_profiel != ALLE:
        cursus_ids_voor_profiel = profiel_cursus_ids.get(filter_profiel, set())
        edities = [e for e in edities if e["cursus_id"] in cursus_ids_voor_profiel]

    if not edities:
        st.info("Geen aankomende edities voor dit profiel.")
        return

    mijn_inschrijvingen = {e["id"] for e in gist_client.get_edities_voor_medewerker(naam)}

    for editie in edities:
        cursus = cursus_lookup.get(editie["cursus_id"], {})
        cursus_naam = cursus.get("naam", editie["cursus_id"])
        cursus_label = f"{cursus.get('icon', '📋')} {cursus_naam}"
        bezet = len(editie["deelnemers"])
        max_d = editie["max_deelnemers"]
        vrij = max(0, max_d - bezet)
        is_vol = vrij == 0
        is_ingeschreven = editie["id"] in mijn_inschrijvingen
        na_deadline = (date.fromisoformat(eerste_datum(editie)) - vandaag).days < 7

        with st.container(border=True):
            col_info, col_acties = st.columns([3, 2])

            with col_info:
                st.markdown(f"**{cursus_label}**")
                st.caption(editie["naam"])
                for sessie in editie["sessies"]:
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

                    ics_inhoud = genereer_ics_editie(editie, cursus_naam)
                    st.download_button(
                        "📥 Download .ics",
                        data=ics_inhoud,
                        file_name=f"{editie['id']}.ics",
                        mime="text/calendar",
                        key=f"ics_{editie['id']}",
                        use_container_width=True,
                    )

                    annuleer_label = "Annuleren (deadline verstreken)" if na_deadline else "Afmelden"
                    if st.button(
                        annuleer_label,
                        key=f"annuleer_{editie['id']}",
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
                    if st.button(
                        "Inschrijven" if not is_vol else "Vol",
                        key=f"inschr_{editie['id']}",
                        disabled=is_vol,
                        type="primary" if not is_vol else "secondary",
                        use_container_width=True,
                    ):
                        try:
                            gist_client.inschrijven_editie(editie["id"], naam)
                            _verstuur_bevestiging(plan, naam, editie, cursus_naam)
                            st.success("✓ Ingeschreven! Download hieronder je agenda-uitnodiging.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))


def _verstuur_bevestiging(plan: dict, naam: str, editie: dict, cursus_naam: str) -> None:
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
        stuur_bevestigingsmail(naam, email, editie, cursus_naam, smtp_config)
    except Exception:
        pass
