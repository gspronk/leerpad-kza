# views/home.py
import streamlit as st
from datetime import date
from data.milestones import hoogste_mijlpaal
from data.sessie_utils import genereer_ics_editie, stuur_bevestigingsmail
from data.profielen import PROFIEL_KLEUREN, PROFIEL_LABELS


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    profiel = plan.get("profiel", "engineer")
    kleur = PROFIEL_KLEUREN.get(profiel, "#0072B8")
    label = PROFIEL_LABELS.get(profiel, profiel)
    geselecteerd = plan.get("geselecteerd", [])
    statussen = plan.get("statussen", {})

    cursus_lookup: dict = {
        item["id"]: item
        for secties in data.get("blokken", {}).values()
        for sectie in secties
        for item in sectie.get("items", [])
    }
    kern_cursus_ids: set = {
        item["id"]
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
        if item.get("kern")
    }

    afgerond_count = sum(1 for s in statussen.values() if s == "afgerond")
    totaal = len(geselecteerd)
    pct = int(afgerond_count / totaal * 100) if totaal else 0
    huidige_fase = _bepaal_huidige_fase(plan, data)
    fase_label = f"Fase {huidige_fase['num']} — {huidige_fase['naam']}" if huidige_fase else ""

    st.markdown(
        f"""
        <div style="background:{kleur};border-radius:10px;padding:18px 20px;
                    color:#fff;margin-bottom:16px;">
          <div style="font-size:13px;opacity:.8;margin-bottom:4px;">
            Jouw voortgang · {label}
          </div>
          <div style="font-size:22px;font-weight:700;">
            {afgerond_count} van {totaal} cursussen afgerond
          </div>
          <div style="background:rgba(255,255,255,.25);border-radius:4px;
                      height:8px;margin-top:10px;">
            <div style="background:#fff;border-radius:4px;height:8px;width:{pct}%;"></div>
          </div>
          <div style="font-size:12px;opacity:.7;margin-top:6px;">
            {pct}%{"  ·  " + fase_label if fase_label else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    vandaag = date.today()
    alle_edities = gist_client.read_edities().get("edities", [])
    editie, is_ingeschreven = _bepaal_editie_kaart(
        plan, naam, alle_edities, kern_cursus_ids, vandaag
    )
    mijlpaal = hoogste_mijlpaal(plan, data)
    volgende_stap = _bepaal_volgende_stap(plan, cursus_lookup)

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("**Volgende stap**")
            if volgende_stap:
                st.markdown(
                    f"**{volgende_stap.get('icon', '')} {volgende_stap['naam']}**"
                )
                st.caption(volgende_stap.get("duur", ""))
            else:
                st.caption("Geen cursussen gepland.")

    with col2:
        if editie:
            _render_editie_kaart(
                editie, is_ingeschreven, cursus_lookup, kleur,
                naam, gist_client, plan, vandaag,
            )

    with col3:
        if mijlpaal:
            with st.container(border=True):
                st.markdown(f"**{mijlpaal.icon} Mijlpaal behaald!**")
                st.markdown(f"**{mijlpaal.label}**")

    aanbevelingen = _bepaal_aanbevelingen(plan, data)
    if aanbevelingen:
        st.divider()
        st.markdown("**💡 Aanbevolen voor jou**")
        st.caption(
            "Kern-cursussen voor jouw profiel die je nog niet hebt geselecteerd."
        )
        st.markdown(
            "  ".join(
                f"`{item.get('icon', '')} {item['naam']}`" for item in aanbevelingen
            )
        )


def _render_editie_kaart(
    editie: dict,
    is_ingeschreven: bool,
    cursus_lookup: dict,
    kleur: str,
    naam: str,
    gist_client,
    plan: dict,
    vandaag: date,
) -> None:
    cursus = cursus_lookup.get(editie["cursus_id"], {})
    cursus_naam = cursus.get("naam", editie["cursus_id"])
    eerste_sessie = editie["sessies"][0] if editie["sessies"] else {}
    datum_str = eerste_sessie.get("datum", "")
    datum_kleur = kleur if is_ingeschreven else "var(--text-muted, #888)"
    na_deadline = (
        (date.fromisoformat(datum_str) - vandaag).days < 7 if datum_str else True
    )

    with st.container(border=True):
        st.markdown("**Aankomende editie**")
        st.markdown(f"**{cursus.get('icon', '📋')} {cursus_naam}**")
        st.markdown(
            f"<div style='font-size:22px;font-weight:700;color:{datum_kleur};'>"
            f"{datum_str}</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"🕐 {eerste_sessie.get('tijd', '–')}  ·  "
            f"📍 {eerste_sessie.get('locatie', '–')}"
        )
        if is_ingeschreven:
            ics = genereer_ics_editie(editie, cursus_naam)
            st.download_button(
                "📥 Download .ics",
                data=ics,
                file_name=f"{editie['id']}.ics",
                mime="text/calendar",
                key=f"home_ics_{editie['id']}",
                use_container_width=True,
            )
            annuleer_label = (
                "Annuleren (deadline verstreken)" if na_deadline else "Afmelden"
            )
            if st.button(
                annuleer_label,
                key=f"home_annuleer_{editie['id']}",
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
            vrij = max(0, editie["max_deelnemers"] - len(editie["deelnemers"]))
            is_vol = vrij == 0
            if st.button(
                "Inschrijven" if not is_vol else "Vol",
                key=f"home_inschr_{editie['id']}",
                disabled=is_vol,
                type="primary" if not is_vol else "secondary",
                use_container_width=True,
            ):
                try:
                    gist_client.inschrijven_editie(editie["id"], naam)
                    _verstuur_bevestiging(plan, naam, editie, cursus_naam)
                    st.success("✓ Ingeschreven!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def _verstuur_bevestiging(
    plan: dict, naam: str, editie: dict, cursus_naam: str
) -> None:
    email = plan.get("email", "").strip()
    if not email:
        return
    smtp_config = {
        "host": st.secrets.get("SMTP_HOST", "smtp.office365.com"),
        "port": int(st.secrets.get("SMTP_PORT", 587)),
        "user": st.secrets["SMTP_USER"],
        "password": st.secrets["SMTP_PASSWORD"],
    }
    try:
        stuur_bevestigingsmail(naam, email, editie, cursus_naam, smtp_config)
    except Exception as e:
        st.warning(
            f"Inschrijving gelukt, maar bevestigingsmail kon niet verzonden worden. ({e})"
        )


def _bepaal_editie_kaart(
    plan: dict,
    naam: str,
    alle_edities: list,
    kern_cursus_ids: set,
    vandaag: date,
) -> tuple:
    geselecteerd = set(plan.get("geselecteerd", []))
    toekomst = sorted(
        [
            e for e in alle_edities
            if e.get("sessies") and e["sessies"][0]["datum"] >= vandaag.isoformat()
        ],
        key=lambda e: e["sessies"][0]["datum"],
    )
    for e in toekomst:
        if naam in e["deelnemers"]:
            return e, True
    for e in toekomst:
        if e["cursus_id"] in geselecteerd:
            return e, False
    for e in toekomst:
        if e["cursus_id"] in kern_cursus_ids:
            return e, False
    return None, False


def _bepaal_aanbevelingen(plan: dict, data: dict, max_items: int = 3) -> list:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    resultaat = []
    for sectie in data.get("blokken", {}).get(profiel, []):
        for item in sectie.get("items", []):
            if item.get("kern") and item["id"] not in geselecteerd:
                resultaat.append(item)
                if len(resultaat) >= max_items:
                    return resultaat
    return resultaat


def _bepaal_huidige_fase(plan: dict, data: dict):
    profiel = plan.get("profiel", "engineer")
    afgerond = {iid for iid, s in plan.get("statussen", {}).items() if s == "afgerond"}
    fases = data.get("fases", {}).get(profiel, [])
    for fase in fases:
        fase_items = set(fase.get("items", []))
        if fase_items and not fase_items.issubset(afgerond):
            return fase
    return fases[-1] if fases else None


def _bepaal_volgende_stap(plan: dict, cursus_lookup: dict):
    statussen = plan.get("statussen", {})
    for iid in plan.get("geselecteerd", []):
        if statussen.get(iid, "gepland") == "gepland":
            return cursus_lookup.get(iid)
    return None
