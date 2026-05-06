# views/tijdlijn.py
import streamlit as st

PROFIEL_LABELS = {
    "engineer": "QA Engineer",
    "enabler":  "QA Enabler",
    "academy":  "KZAcademy",
    "maatwerk": "Op maat",
    "security": "Security",
}

PROFIEL_KLEUREN = {
    "engineer": "#0072B8",
    "enabler":  "#E5007D",
    "academy":  "#F0A500",
    "maatwerk": "#A371F7",
    "security": "#FF6B35",
}


def render(data: dict, plan: dict) -> None:
    geselecteerd = set(plan.get("geselecteerd", []))
    statussen    = plan.get("statussen", {})

    alle_profielen = list(data.get("profielen", {}).keys())
    gekozen = st.radio(
        "Tijdlijn voor",
        options=alle_profielen,
        format_func=lambda k: PROFIEL_LABELS.get(k, k),
        horizontal=True,
        index=alle_profielen.index(plan.get("profiel", "engineer")) if plan.get("profiel") in alle_profielen else 0,
    )

    fases = data.get("fases", {}).get(gekozen, [])
    alle_items = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }
    kleur = PROFIEL_KLEUREN.get(gekozen, "#0072B8")

    if not fases:
        st.info("Geen tijdlijn beschikbaar voor dit profiel.")
        return

    st.divider()

    for fase in fases:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
            f'<span style="font-family:monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;'
            f'padding:3px 10px;border-radius:99px;background:{kleur}22;color:{kleur};border:1px solid {kleur}44">'
            f'Fase {fase["num"]}</span>'
            f'<span style="font-weight:700;color:#f0f6ff;font-size:16px">{fase.get("naam", fase.get("name", ""))}</span>'
            f'<span style="font-size:11px;color:#8b949e">{fase.get("desc","")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        fase_prefix = fase.get("prefix", [])
        fase_items = [
            alle_items[iid]
            for iid in alle_items
            if any(iid.startswith(p) for p in fase_prefix)
        ]

        if not fase_items:
            st.caption("*Geen blokken in deze fase.*")
            continue

        cols = st.columns(min(len(fase_items), 4))
        for idx, item in enumerate(fase_items):
            with cols[idx % len(cols)]:
                is_sel = item["id"] in geselecteerd
                status = statussen.get(item["id"], "gepland")
                status_kleur = {"afgerond": "#39D353", "bezig": "#F0A500"}.get(status, "#30363D")
                border = kleur if is_sel else "#21262D"

                kern_badge = "<div style='font-size:9px;color:#E5007D'>★</div>" if item.get("kern") else ""

                st.markdown(
                    f'<div style="background:#0d1117;border:1px solid {border};border-top:3px solid {status_kleur};'
                    f'border-radius:8px;padding:10px;margin-bottom:6px;min-height:80px">'
                    f'<div style="font-size:16px">{item.get("icon","")}</div>'
                    f'<div style="font-weight:700;color:#f0f6ff;font-size:11px;margin:4px 0">{item["naam"]}</div>'
                    f'<div style="font-size:9px;color:#8b949e">{item.get("duur","")}</div>'
                    f'{kern_badge}'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.divider()
