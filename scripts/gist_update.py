"""
Upload lokale cursussen.json naar GitHub Gist.
Gebruik: python scripts/gist_update.py

Leest GITHUB_TOKEN en GIST_ID uit .streamlit/secrets.toml.
"""
import json
import sys
import os
import tomllib
from pathlib import Path

# Voeg projectroot toe aan sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.gist import GistClient


def laad_secrets() -> dict:
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"FOUT: {secrets_path} niet gevonden.")
        print("Kopieer .streamlit/secrets.toml.example naar .streamlit/secrets.toml en vul je token en gist-ID in.")
        sys.exit(1)
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def main():
    secrets = laad_secrets()
    token    = secrets.get("GITHUB_TOKEN", "")
    gist_id  = secrets.get("GIST_ID", "")

    if not token or token.startswith("ghp_xxxx"):
        print("FOUT: GITHUB_TOKEN is niet ingevuld in secrets.toml.")
        sys.exit(1)
    if not gist_id or gist_id.startswith("abc123"):
        print("FOUT: GIST_ID is niet ingevuld in secrets.toml.")
        sys.exit(1)

    cursussen_path = Path(__file__).parent.parent / "cursussen.json"
    if not cursussen_path.exists():
        print(f"FOUT: {cursussen_path} niet gevonden.")
        sys.exit(1)

    with open(cursussen_path, encoding="utf-8") as f:
        data = json.load(f)

    totaal = sum(
        len(sectie["items"])
        for blokken in data["blokken"].values()
        for sectie in blokken
    )

    print(f"Uploaden naar Gist {gist_id[:8]}...")
    print(f"  {len(data['profielen'])} profielen, {totaal} cursussen")

    client = GistClient(token=token, gist_id=gist_id)
    client.write_cursussen(data)

    print("Klaar! cursussen.json staat nu in de Gist.")


if __name__ == "__main__":
    main()
