# scripts/migrate.py
"""
Eenmalig migratiescript: extraheert data uit kza_leerpad_verkenner.html
en schrijft cursussen.json.

Gebruik: python scripts/migrate.py --html pad/naar/kza_leerpad_verkenner.html --out cursussen.json
"""
import argparse
import json
import re


def transform_profiles(raw: dict) -> dict:
    """Hernoem velden naar NL-namen en verwijder 'accent'."""
    result = {}
    for key, val in raw.items():
        result[key] = {
            "kleur": val.get("color", ""),
            "titel": val.get("title", ""),
            "sub":   val.get("sub", ""),
        }
    return result


def transform_blocks(raw: dict) -> dict:
    """Hernoem section→sectie, name→naam, dur→duur per item."""
    result = {}
    for profiel, secties in raw.items():
        result[profiel] = []
        for sectie in secties:
            nieuwe_sectie = {
                "sectie": sectie.get("section", sectie.get("sectie", "")),
                "badge":  sectie.get("badge", ""),
                "items":  []
            }
            for item in sectie.get("items", []):
                nieuw_item = {
                    "id":    item["id"],
                    "naam":  item.get("name", item.get("naam", "")),
                    "icon":  item.get("icon", ""),
                    "desc":  item.get("desc", ""),
                    "tags":  item.get("tags", []),
                    "duur":  item.get("dur", item.get("duur", "")),
                    "kern":  item.get("kern", False),
                    "cross": item.get("cross", []),
                }
                nieuwe_sectie["items"].append(nieuw_item)
            result[profiel].append(nieuwe_sectie)
    return result


def extract_js_object(html: str, varname: str) -> dict:
    """
    Haalt een JS-object (const VARNAME = {...};) op uit HTML via json parsing
    na lichte normalisatie.
    """
    pattern = rf"(?:const|var)\s+{varname}\s*=\s*(\{{[\s\S]*?\}});\s*\n"
    match = re.search(pattern, html)
    if not match:
        raise ValueError(f"Variabele {varname} niet gevonden in HTML")
    js_obj = match.group(1)
    # Normaliseer JS naar JSON: verwijder trailing commas, vervang single quotes
    js_obj = re.sub(r",(\s*[}\]])", r"\1", js_obj)  # trailing commas
    js_obj = re.sub(r"'([^']*)'", r'"\1"', js_obj)  # single → double quotes
    js_obj = re.sub(r"(\w+):", r'"\1":', js_obj)    # unquoted keys
    js_obj = re.sub(r'"(\w+)":', lambda m: f'"{m.group(1)}":', js_obj)
    try:
        return json.loads(js_obj)
    except json.JSONDecodeError as e:
        raise ValueError(f"Kon {varname} niet parsen als JSON: {e}")


def migrate(html_path: str, out_path: str) -> None:
    # Gebruik Node.js voor betrouwbare JS-extractie
    import subprocess
    import tempfile
    import os

    # Resolve to absolute path so Node.js (running from temp dir) can find it
    html_path = os.path.abspath(html_path)

    with open(html_path, encoding="utf-8") as f:
        html = f.read()  # noqa: F841 — kept for potential fallback use

    node_script = """
const vm = require('vm');
const html = require('fs').readFileSync(process.argv[2], 'utf8');
// Find the bare <script> tag (without src attribute) that contains the data
const scripts = [...html.matchAll(/<script(?![^>]*src)[^>]*>([\\s\\S]*?)<\\/script>/g)];
const dataScript = scripts.find(m => m[1].includes('PROFILES'));
if (!dataScript) throw new Error('Could not find data script block');
// Replace const/let with var so vm.runInThisContext exposes vars to outer scope
const code = dataScript[1].split('// STATE')[0]
    .replace(/\\bconst\\b/g, 'var')
    .replace(/\\blet\\b/g, 'var');
vm.runInThisContext(code);
console.log(JSON.stringify({
    profielen: PROFILES,
    blokken: BLOCKS,
    skills: SKILLS,
    fases: PHASE_MAP
}));
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as tmp:
        tmp.write(node_script)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ['node', tmp_path, html_path],
            capture_output=True, text=True, check=True,
            encoding='utf-8'
        )
        raw = json.loads(result.stdout)
    finally:
        os.unlink(tmp_path)

    # Transformeer naar NL-schema
    output = {
        "profielen": transform_profiles(raw["profielen"]),
        "blokken":   transform_blocks(raw["blokken"]),
        "skills":    raw["skills"],
        "fases":     raw["fases"],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"OK Geschreven naar {out_path}")
    totaal = sum(
        len(sectie["items"])
        for blokken in output["blokken"].values()
        for sectie in blokken
    )
    print(f"  {len(output['profielen'])} profielen, {totaal} cursussen")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--out", default="cursussen.json")
    args = parser.parse_args()
    migrate(args.html, args.out)
