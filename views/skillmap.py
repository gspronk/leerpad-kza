# views/skillmap.py
import streamlit as st


def render(data: dict, plan: dict) -> None:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))

    skill_cats = data.get("skills", {}).get(profiel, [])

    if not skill_cats:
        st.info("Geen skill map beschikbaar voor dit profiel.")
        return

    cols = st.columns(3)
    for idx, cat in enumerate(skill_cats):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{cat.get('icon','')} {cat['cat']}**")
                for skill in cat.get("items", []):
                    gerelateerd = skill.get("rel", [])
                    actief = sum(1 for r in gerelateerd if r in geselecteerd)
                    totaal = len(gerelateerd)

                    pips_html = ""
                    for i in range(min(totaal, 5)):
                        kleur = "#0072B8" if i < actief else "#21262D"
                        pips_html += f'<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:{kleur};margin-right:2px"></span>'

                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #21262d;font-size:12px">'
                        f'<span style="color:#CDD9E5">{skill["nm"]}</span>'
                        f'<span>{pips_html}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
