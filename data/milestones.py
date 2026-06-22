from dataclasses import dataclass


@dataclass
class Mijlpaal:
    id: str
    label: str
    icon: str
    prioriteit: int  # hogere waarde = hogere mijlpaal


def bereken_mijlpalen(plan: dict, data: dict) -> list:
    profiel = plan.get("profiel", "engineer")
    geselecteerd = set(plan.get("geselecteerd", []))
    afgerond = {iid for iid, s in plan.get("statussen", {}).items() if s == "afgerond"}
    resultaat = []

    if len(afgerond) >= 1:
        resultaat.append(Mijlpaal(
            id="eerste_cursus",
            label="Eerste cursus afgerond",
            icon="🎉",
            prioriteit=1,
        ))

    for fase in data.get("fases", {}).get(profiel, []):
        fase_items = set(fase.get("items", []))
        if fase_items and fase_items.issubset(afgerond):
            resultaat.append(Mijlpaal(
                id=f"fase_{fase['num']}_voltooid",
                label=f"Fase {fase['num']} voltooid — {fase['naam']}",
                icon="🏅",
                prioriteit=10 + fase["num"],
            ))

    kern_ids = {
        item["id"]
        for sectie in data.get("blokken", {}).get(profiel, [])
        for item in sectie.get("items", [])
        if item.get("kern")
    }
    if kern_ids and kern_ids.issubset(afgerond):
        resultaat.append(Mijlpaal(
            id="alle_kern",
            label="Alle kern-cursussen afgerond",
            icon="⭐",
            prioriteit=50,
        ))

    if geselecteerd and geselecteerd.issubset(afgerond):
        resultaat.append(Mijlpaal(
            id="leerplan_volledig",
            label="Leerplan volledig afgerond",
            icon="🏆",
            prioriteit=100,
        ))

    return sorted(resultaat, key=lambda m: m.prioriteit)


def hoogste_mijlpaal(plan: dict, data: dict):
    mijlpalen = bereken_mijlpalen(plan, data)
    return mijlpalen[-1] if mijlpalen else None
