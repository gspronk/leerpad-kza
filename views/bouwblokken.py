# views/bouwblokken.py
import streamlit as st
from datetime import date


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    statussen = plan.get("statussen", {})

    blokken = data.get("blokken", {})
    profiel_blokken = blokken.get(profiel, [])

    # Cross-functionele toggle
    cross_on = st.toggle("Toon ook cross-functionele bouwblokken van andere profielen", key="cross_toggle")

    # Verzamel cross-functionele items als toggle aan staat
    cross_items: set[str] = set()
    if cross_on:
        for andere_profiel, secties in blokken.items():
            if andere_profiel == profiel:
                continue
            for sectie in secties:
                for item in sectie.get("items", []):
                    if profiel in item.get("cross", []):
                        cross_items.add(item["id"])

    wijziging = False

    for sectie in profiel_blokken:
        st.markdown(f"### {sectie['sectie']}")
        kern_items = [i for i in sectie["items"] if i.get("kern")]
        opt_items  = [i for i in sectie["items"] if not i.get("kern")]

        if kern_items:
            st.markdown("**★ Essentieel**")
            cols = st.columns(3)
            for idx, item in enumerate(kern_items):
                with cols[idx % 3]:
                    if _render_blok_card(item, geselecteerd, statussen, cross_items):
                        if item["id"] in geselecteerd:
                            geselecteerd.discard(item["id"])
                            statussen.pop(item["id"], None)
                        else:
                            geselecteerd.add(item["id"])
                            statussen[item["id"]] = "gepland"
                        wijziging = True

        if opt_items:
            st.markdown("*Optioneel*")
            cols = st.columns(3)
            for idx, item in enumerate(opt_items):
                with cols[idx % 3]:
                    if _render_blok_card(item, geselecteerd, statussen, cross_items):
                        if item["id"] in geselecteerd:
                            geselecteerd.discard(item["id"])
                            statussen.pop(item["id"], None)
                        else:
                            geselecteerd.add(item["id"])
                            statussen[item["id"]] = "gepland"
                        wijziging = True

    # Cross-functionele blokken van andere profielen
    if cross_on and cross_items:
        st.divider()
        st.markdown("### 🔀 Cross-functioneel")
        cross_cols = st.columns(3)
        col_idx = 0
        for andere_profiel, secties in blokken.items():
            if andere_profiel == profiel:
                continue
            for sectie in secties:
                for item in sectie["items"]:
                    if item["id"] in cross_items:
                        with cross_cols[col_idx % 3]:
                            if _render_blok_card(item, geselecteerd, statussen, cross_items, cross_label=andere_profiel):
                                if item["id"] in geselecteerd:
                                    geselecteerd.discard(item["id"])
                                    statussen.pop(item["id"], None)
                                else:
                                    geselecteerd.add(item["id"])
                                    statussen[item["id"]] = "gepland"
                                wijziging = True
                        col_idx += 1

    if wijziging:
        plan["geselecteerd"] = list(geselecteerd)
        plan["statussen"] = statussen
        plan["laatst_actief"] = str(date.today())
        st.session_state["plan"] = plan
        gist_client.save_plan(naam, plan)
        st.rerun()


def _render_blok_card(item: dict, geselecteerd: set, statussen: dict,
                       cross_items: set, cross_label: str = "") -> bool:
    """Rendert een blok-card. Geeft True terug als de gebruiker erop klikt."""
    is_sel = item["id"] in geselecteerd
    status = statussen.get(item["id"], "gepland")
    is_cross = item["id"] in cross_items

    border_kleur = "#0072B8" if is_sel and not is_cross else ("#A371F7" if is_cross else "#21262D")
    achtergrond  = "#0d1117" if not is_sel else "#161B22"

    tags_html = " ".join(f'<span style="font-size:9px;background:#21262d;padding:1px 5px;border-radius:3px;color:#8b949e">{t}</span>' for t in item.get("tags", []))
    kern_badge = '<span style="font-size:9px;color:#E5007D">★ Essentieel</span>' if item.get("kern") else ""
    cross_badge = f'<span style="font-size:9px;color:#A371F7">↔ {cross_label}</span>' if cross_label else ""
    check = "✓" if is_sel else "○"

    st.markdown(f"""
    <div style="background:{achtergrond};border:1px solid {border_kleur};
                border-radius:8px;padding:12px;margin-bottom:6px">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
            <span style="font-size:18px">{item.get('icon','')}</span>
            <span style="color:{'#0072B8' if is_sel else '#8b949e'}">{check}</span>
        </div>
        <div style="font-weight:700;color:#f0f6ff;font-size:13px;margin-bottom:4px">{item['naam']}</div>
        <div style="font-size:11px;color:#8b949e;line-height:1.5;margin-bottom:6px">{item.get('desc','')}</div>
        <div style="margin-bottom:4px">{tags_html}</div>
        <div style="font-size:10px;color:#8b949e">{item.get('duur','')}</div>
        <div style="margin-top:4px">{kern_badge} {cross_badge}</div>
    </div>
    """, unsafe_allow_html=True)

    return st.button(
        "Verwijder" if is_sel else "Toevoegen",
        key=f"blok_{item['id']}",
        use_container_width=True
    )
