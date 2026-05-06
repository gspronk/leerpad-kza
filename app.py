# app.py
import streamlit as st
from data.gist import GistClient
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="KZA Leerpad Verkenner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_gist_client() -> GistClient:
    return GistClient(
        token=st.secrets["GITHUB_TOKEN"],
        gist_id=st.secrets["GIST_ID"],
    )


def main():
    client = get_gist_client()
    naam, profiel, plan = render_sidebar(client)

    if naam is None:
        st.info("👈 Log in via de sidebar om te beginnen.")
        st.stop()

    # Laad catalogus
    data = client.read_cursussen()

    # 7 tabs
    tabs = st.tabs([
        "◈ Bouwblokken",
        "→ Roadmap",
        "◉ Skill Map",
        "★ Mijn Plan",
        "≡ Alle cursussen",
        "⏱ Tijdlijn",
        "⚙️ Beheer",
    ])

    with tabs[0]:
        from views.bouwblokken import render as render_bouwblokken
        render_bouwblokken(data, plan, client, naam)

    with tabs[1]:
        from views.roadmap import render as render_roadmap
        render_roadmap(data, plan)

    with tabs[2]:
        from views.skillmap import render as render_skillmap
        render_skillmap(data, plan)

    with tabs[3]:
        from views.mijn_plan import render as render_plan
        render_plan(data, plan, client, naam)

    with tabs[4]:
        from views.alle_cursussen import render as render_overzicht
        render_overzicht(data, plan)

    with tabs[5]:
        from views.tijdlijn import render as render_tijdlijn
        render_tijdlijn(data, plan)

    with tabs[6]:
        from views.beheer import render as render_beheer
        render_beheer(data, client)


if __name__ == "__main__":
    main()
