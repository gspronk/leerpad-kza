# views/mijn_plan.py
import streamlit as st
from datetime import date
from components.export_pptx import generate_pptx
from data.milestones import bereken_mijlpalen

STATUS_OPTIES = ["gepland", "bezig", "afgerond"]
STATUS_LABELS = {"gepland": "○ Gepland", "bezig": "◉ Bezig", "afgerond": "✓ Afgerond"}


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    geselecteerd = plan.get("geselecteerd", [])
    statussen    = plan.get("statussen", {})

    if not geselecteerd:
        st.info("Je hebt nog geen bouwblokken geselecteerd. Ga naar '◈ Bouwblokken' om te beginnen.")
        return

    alle_items = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    col1, col2, col3 = st.columns(3)
    gepland   = sum(1 for iid in geselecteerd if statussen.get(iid) == "gepland")
    bezig     = sum(1 for iid in geselecteerd if statussen.get(iid) == "bezig")
    afgerond  = sum(1 for iid in geselecteerd if statussen.get(iid) == "afgerond")
    col1.metric("○ Gepland",   gepland)
    col2.metric("◉ Bezig",     bezig)
    col3.metric("✓ Afgerond",  afgerond)

    st.divider()

    wijziging = False
    cols = st.columns(3)
    for idx, iid in enumerate(geselecteerd):
        item = alle_items.get(iid)
        if not item:
            continue
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{item.get('icon','')} {item['naam']}**")
                st.caption(item.get("duur", ""))
                huidige_status = statussen.get(iid, "gepland")
                nieuwe_status = st.selectbox(
                    "Status",
                    options=STATUS_OPTIES,
                    format_func=lambda s: STATUS_LABELS[s],
                    index=STATUS_OPTIES.index(huidige_status),
                    key=f"status_{iid}",
                    label_visibility="collapsed"
                )
                if nieuwe_status != huidige_status:
                    statussen[iid] = nieuwe_status
                    wijziging = True

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

    st.divider()

    col_pptx, col_txt, col_wis = st.columns(3)

    with col_pptx:
        pptx_bytes = generate_pptx(data, plan)
        st.download_button(
            label="📊 Exporteer als PowerPoint",
            data=pptx_bytes,
            file_name=f"kza_leerpad_{naam}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

    with col_txt:
        tekst = _genereer_tekst_export(data, plan, naam)
        st.download_button(
            label="📄 Exporteer als tekst",
            data=tekst,
            file_name=f"kza_leerpad_{naam}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_wis:
        if st.button("🗑 Wis selectie", use_container_width=True):
            if st.session_state.get("wis_bevestigd"):
                plan["geselecteerd"] = []
                plan["statussen"] = {}
                st.session_state["plan"] = plan
                st.session_state["wis_bevestigd"] = False
                gist_client.save_plan(naam, plan)
                st.rerun()
            else:
                st.session_state["wis_bevestigd"] = True
                st.warning("Klik nogmaals om te bevestigen.")


def _genereer_tekst_export(data: dict, plan: dict, naam: str) -> str:
    profiel_key  = plan.get("profiel", "engineer")
    profiel_meta = data.get("profielen", {}).get(profiel_key, {})
    geselecteerd = plan.get("geselecteerd", [])
    statussen    = plan.get("statussen", {})

    alle_items = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    lines = [
        f"KZA Leerpad — {profiel_meta.get('titel', profiel_key)}",
        f"Gebruiker: {naam}",
        f"Datum: {plan.get('laatst_actief', '')}",
        "",
        f"Geselecteerde bouwblokken ({len(geselecteerd)}):",
        "",
    ]
    for iid in geselecteerd:
        item = alle_items.get(iid)
        if item:
            status = statussen.get(iid, "gepland")
            lines.append(f"  [{status.upper()}] {item.get('icon','')} {item['naam']} ({item.get('duur','')})")
    return "\n".join(lines)
