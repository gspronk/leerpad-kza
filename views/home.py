# views/home.py
from datetime import date


def render(data: dict, plan: dict, gist_client, naam: str) -> None:
    pass


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
    return None


def _bepaal_volgende_stap(plan: dict, cursus_lookup: dict):
    return None
