# components/sidebar.py
import streamlit as st
from datetime import date


PROFIEL_META = {
    "engineer": {"label": "QA Engineer",    "kleur": "#0072B8", "icon": "⚙️"},
    "enabler":  {"label": "QA Enabler",     "kleur": "#E5007D", "icon": "🎓"},
    "academy":  {"label": "KZAcademy",      "kleur": "#F0A500", "icon": "📚"},
    "maatwerk": {"label": "Op maat",        "kleur": "#A371F7", "icon": "✨"},
    "security": {"label": "Security",       "kleur": "#FF6B35", "icon": "🔒"},
}


def normalize_naam(naam: str) -> str:
    return naam.strip().lower()


def kern_ids_voor_profiel(data: dict, profiel: str) -> list[str]:
    """Geeft alle item-IDs met kern=True voor het gegeven profiel."""
    return [
        item["id"]
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
        if item.get("kern", False)
    ]


def render_sidebar(gist_client) -> tuple[str | None, str, dict]:
    """
    Rendert de volledige sidebar.
    Returns: (naam | None, profiel, plan_dict)
    Als naam None is, is de gebruiker nog niet ingelogd.
    """
    with st.sidebar:
        # Logo
        st.markdown("## KZA")
        st.caption("Leerpad Verkenner")
        st.divider()

        naam, profiel, plan = _handle_login(gist_client)

        if naam:
            _render_profiel_knoppen(profiel)
            _render_voortgang(plan)
            _render_persoonlijke_link(naam)

    return naam, profiel, plan


def _handle_login(gist_client) -> tuple[str | None, str, dict]:
    """
    Behandelt de login-flow. Checkt eerst URL-param,
    dan session_state, dan toont het aanmeldscherm.
    """
    # 1. URL-param check
    query_naam = st.query_params.get("naam", "")
    if query_naam:
        return _laad_gebruiker(gist_client, query_naam)

    # 2. Session state
    if "naam" in st.session_state and st.session_state["naam"]:
        naam = st.session_state["naam"]
        profiel = st.session_state.get("profiel", "engineer")
        plan = st.session_state.get("plan", {})
        return naam, profiel, plan

    # 3. Aanmeldscherm
    _render_aanmeldscherm(gist_client)
    return None, "engineer", {}


def _laad_gebruiker(gist_client, naam: str) -> tuple[str, str, dict]:
    plan = gist_client.get_plan(naam)
    profiel = plan.get("profiel", "engineer")

    st.session_state["naam"] = naam
    st.session_state["profiel"] = profiel
    st.session_state["plan"] = plan
    return naam, profiel, plan


def _render_aanmeldscherm(gist_client) -> None:
    st.markdown("### 👋 Welkom")
    st.caption("Kies je naam of maak een nieuw profiel aan.")

    gebruikers = gist_client.lijst_gebruikers()

    if gebruikers:
        opties = {f"👤 {g['naam']}  —  {PROFIEL_META.get(g['profiel'], {}).get('label', g['profiel'])}": g['naam']
                  for g in gebruikers}
        keuze_label = st.selectbox("Bestaande gebruiker", ["— kies je naam —"] + list(opties.keys()))

        if keuze_label != "— kies je naam —":
            gekozen_naam = opties[keuze_label]
            if st.button(f"→ Inloggen als {gekozen_naam}", use_container_width=True):
                st.query_params["naam"] = gekozen_naam
                st.rerun()

        st.markdown("---")

    # Nieuw profiel
    if st.button("✨ Nieuw profiel aanmaken", use_container_width=True):
        st.session_state["toon_nieuw_formulier"] = True

    if st.session_state.get("toon_nieuw_formulier"):
        _render_nieuw_profiel_formulier(gist_client)


def _render_nieuw_profiel_formulier(gist_client) -> None:
    st.markdown("#### Nieuw profiel")
    nieuwe_naam = st.text_input("Jouw naam", key="nieuwe_naam_input")

    profiel_keuze = st.radio(
        "Startprofiel",
        options=list(PROFIEL_META.keys()),
        format_func=lambda k: f"{PROFIEL_META[k]['icon']} {PROFIEL_META[k]['label']}",
        horizontal=True,
        key="nieuw_profiel_keuze"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Aanmaken", use_container_width=True):
            if not nieuwe_naam.strip():
                st.error("Naam mag niet leeg zijn.")
                return
            # Controleer of naam al bestaat
            bestaand = gist_client.get_plan(nieuwe_naam)
            if bestaand:
                st.error(f"Naam '{nieuwe_naam.strip()}' bestaat al. Kies een andere naam.")
                return
            # Maak nieuw plan aan met kernblokken
            cursussen = gist_client.read_cursussen()
            kern_ids = kern_ids_voor_profiel(cursussen, profiel_keuze)
            nieuw_plan = {
                "profiel": profiel_keuze,
                "geselecteerd": kern_ids,
                "statussen": {kid: "gepland" for kid in kern_ids},
                "laatst_actief": str(date.today()),
            }
            gist_client.save_plan(nieuwe_naam.strip(), nieuw_plan)
            st.query_params["naam"] = nieuwe_naam.strip()
            st.rerun()
    with col2:
        if st.button("← Terug", use_container_width=True):
            st.session_state["toon_nieuw_formulier"] = False
            st.rerun()


def _render_profiel_knoppen(huidig_profiel: str) -> None:
    st.markdown("**Profiel**")
    for key, meta in PROFIEL_META.items():
        actief = key == huidig_profiel
        label = f"{'●' if actief else '○'} {meta['label']}"
        if st.button(label, key=f"profiel_btn_{key}", use_container_width=True):
            st.session_state["profiel"] = key
            # Update profiel in plan
            plan = st.session_state.get("plan", {})
            plan["profiel"] = key
            st.session_state["plan"] = plan
            st.rerun()
    st.divider()


def _render_voortgang(plan: dict) -> None:
    geselecteerd = plan.get("geselecteerd", [])
    statussen = plan.get("statussen", {})
    afgerond = sum(1 for s in statussen.values() if s == "afgerond")
    totaal = len(geselecteerd)

    if totaal > 0:
        st.metric("Geselecteerd", f"{totaal} blokken")
        st.progress(afgerond / totaal if totaal else 0, text=f"{afgerond} afgerond")
    st.divider()


def _render_persoonlijke_link(naam: str) -> None:
    base_url = st.secrets.get("APP_URL", "http://localhost:8501")
    link = f"{base_url}?naam={naam}"
    st.caption("🔗 Jouw persoonlijke link")
    st.code(link, language=None)
