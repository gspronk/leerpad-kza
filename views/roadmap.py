# views/roadmap.py
import streamlit as st

STATUS_KLEUR = {
    "afgerond": "#39D353",
    "bezig":    "#F0A500",
    "gepland":  "#8B949E",
}

STATUS_LABEL = {
    "afgerond": "✓ Afgerond",
    "bezig":    "◉ Bezig",
    "gepland":  "○ Gepland",
}


def render(data: dict, plan: dict) -> None:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    statussen = plan.get("statussen", {})

    fases = data.get("fases", {}).get(profiel, [])
    alle_items = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }

    if not fases:
        st.info("Geen roadmap beschikbaar voor dit profiel.")
        return

    for fase in fases:
        col_spine, col_card = st.columns([1, 12])
        with col_spine:
            st.markdown(f"<div style='text-align:center;padding-top:18px'><div style='width:11px;height:11px;border-radius:50%;background:#E5007D;margin:auto'></div></div>", unsafe_allow_html=True)

        with col_card:
            with st.container(border=True):
                st.markdown(f"<span style='font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#E5007D'>Fase {fase['num']}</span>", unsafe_allow_html=True)
                st.markdown(f"**{fase.get('naam', fase.get('name', ''))}**")
                st.caption(fase.get("desc", ""))

                # Toon items voor deze fase op basis van prefix
                fase_prefix = fase.get("prefix", [])
                fase_items = [
                    alle_items[iid]
                    for iid in geselecteerd
                    if iid in alle_items and any(iid.startswith(p) for p in fase_prefix)
                ]

                if fase_items:
                    pills_html = ""
                    for item in fase_items:
                        st_key = statussen.get(item["id"], "gepland")
                        kleur = STATUS_KLEUR[st_key]
                        label = STATUS_LABEL[st_key]
                        pills_html += f'<span style="border:1px solid {kleur};color:{kleur};background:{kleur}11;padding:3px 10px;border-radius:99px;font-size:11px;margin:2px;display:inline-block">{item["icon"]} {item["naam"]} — {label}</span> '
                    st.markdown(pills_html, unsafe_allow_html=True)
                else:
                    st.caption("*Geen blokken geselecteerd voor deze fase.*")
