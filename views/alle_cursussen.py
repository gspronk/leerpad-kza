# views/alle_cursussen.py
import streamlit as st

PROFIEL_LABELS = {
    "engineer": "QA Engineer",
    "enabler":  "QA Enabler",
    "academy":  "KZAcademy",
    "maatwerk": "Op maat",
    "security": "Security",
}


def render(data: dict, plan: dict) -> None:
    geselecteerd = set(plan.get("geselecteerd", []))

    alle_items = []
    for profiel, secties in data.get("blokken", {}).items():
        for sectie in secties:
            for item in sectie.get("items", []):
                alle_items.append({**item, "_profiel": profiel, "_sectie": sectie["sectie"]})

    zoekterm = st.text_input("🔍 Zoek op naam, beschrijving of tag", placeholder="bijv. Playwright")

    cols = st.columns(6)
    actieve_profielen: set[str] = set()
    for idx, (key, label) in enumerate(PROFIEL_LABELS.items()):
        with cols[idx]:
            if st.toggle(label, key=f"filter_{key}", value=True):
                actieve_profielen.add(key)

    gefilterd = [
        item for item in alle_items
        if item["_profiel"] in actieve_profielen
        and (
            not zoekterm
            or zoekterm.lower() in item["naam"].lower()
            or zoekterm.lower() in item.get("desc", "").lower()
            or any(zoekterm.lower() in tag.lower() for tag in item.get("tags", []))
        )
    ]

    st.caption(f"{len(gefilterd)} van {len(alle_items)} cursussen")

    if not gefilterd:
        st.info("Geen cursussen gevonden.")
        return

    header_cols = st.columns([3, 1, 1, 1, 1])
    header_cols[0].markdown("**Naam**")
    header_cols[1].markdown("**Profiel**")
    header_cols[2].markdown("**Duur**")
    header_cols[3].markdown("**Kern**")
    header_cols[4].markdown("**Geselecteerd**")
    st.divider()

    for item in gefilterd:
        row = st.columns([3, 1, 1, 1, 1])
        with row[0]:
            st.markdown(f"**{item.get('icon','')} {item['naam']}**")
            st.caption(item.get("desc", "")[:80])
        row[1].caption(PROFIEL_LABELS.get(item["_profiel"], item["_profiel"]))
        row[2].caption(item.get("duur", ""))
        row[3].caption("★" if item.get("kern") else "—")
        row[4].caption("✓" if item["id"] in geselecteerd else "—")
