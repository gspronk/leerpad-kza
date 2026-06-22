# data/gist.py
import json
import time
from datetime import date
from github import Github

ANNULERING_DEADLINE_DAGEN = 7

CACHE_TTL = 300  # 5 minuten


class GistClient:
    def __init__(self, token: str, gist_id: str):
        self._gh = Github(token)
        self._gist_id = gist_id
        self._gist = None
        self._cursussen_cache: dict | None = None
        self._cursussen_cache_time: float = 0
        self._plannen_cache: dict | None = None
        self._plannen_cache_time: float = 0
        self._cache_ttl: float = CACHE_TTL

    def _get_gist(self):
        if self._gist is None:
            self._gist = self._gh.get_gist(self._gist_id)
        return self._gist

    def _read_file(self, filename: str) -> dict:
        gist = self._gh.get_gist(self._gist_id)  # altijd verse gist voor reads
        self._gist = gist
        file = gist.files.get(filename)
        if file is None:
            raise KeyError(filename)
        return json.loads(file.content)

    def _write_file(self, filename: str, data: dict) -> None:
        from github import InputFileContent
        gist = self._get_gist()
        gist.edit(files={filename: InputFileContent(json.dumps(data, ensure_ascii=False, indent=2))})

    # ── cursussen ──────────────────────────────────────────────

    def read_cursussen(self) -> dict:
        now = time.time()
        if self._cursussen_cache is not None and (now - self._cursussen_cache_time) < self._cache_ttl:
            return self._cursussen_cache
        self._cursussen_cache = self._read_file("cursussen.json")
        self._cursussen_cache_time = time.time()
        return self._cursussen_cache

    def write_cursussen(self, data: dict) -> None:
        self._write_file("cursussen.json", data)
        self._cursussen_cache = None  # invalideer cache
        self._cursussen_cache_time = 0

    # ── plannen ────────────────────────────────────────────────

    def read_plannen(self) -> dict:
        now = time.time()
        if self._plannen_cache is not None and (now - self._plannen_cache_time) < self._cache_ttl:
            return self._plannen_cache
        self._plannen_cache = self._read_file("plannen.json")
        self._plannen_cache_time = time.time()
        return self._plannen_cache

    def write_plannen(self, data: dict) -> None:
        self._write_file("plannen.json", data)
        self._plannen_cache = None  # invalideer cache
        self._plannen_cache_time = 0

    def get_plan(self, naam: str) -> dict:
        """Geeft het plan voor naam (case-insensitive, getrimmd). Lege dict als niet gevonden."""
        naam = naam.strip()
        plannen = self.read_plannen()
        for key, plan in plannen.items():
            if key.strip().lower() == naam.lower():
                return plan
        return {}

    def save_plan(self, naam: str, plan: dict) -> None:
        """Slaat het plan op. Gebruikt de bestaande sleutel als die al bestaat (case-insensitive)."""
        naam = naam.strip()
        plannen = self.read_plannen()
        # Zoek bestaande sleutel
        existing_key = next(
            (k for k in plannen if k.strip().lower() == naam.lower()), None
        )
        key = existing_key if existing_key else naam
        plannen[key] = plan
        self.write_plannen(plannen)

    # ── edities ────────────────────────────────────────────────

    def read_edities(self) -> dict:
        try:
            data = self._read_file("sessies.json")
            if "edities" not in data:
                return {"edities": []}
            return data
        except (KeyError, AttributeError, TypeError):
            return {"edities": []}

    def write_edities(self, data: dict) -> None:
        self._write_file("sessies.json", data)

    def _vind_editie(self, data: dict, editie_id: str) -> dict:
        for e in data.get("edities", []):
            if e["id"] == editie_id:
                return e
        raise ValueError(f"Editie '{editie_id}' niet gevonden")

    def inschrijven_editie(self, editie_id: str, naam: str) -> None:
        data = self.read_edities()
        editie = self._vind_editie(data, editie_id)
        if naam in editie["deelnemers"]:
            raise ValueError(f"'{naam}' is al ingeschreven voor deze editie")
        if len(editie["deelnemers"]) >= editie["max_deelnemers"]:
            raise ValueError("Editie is vol")
        editie["deelnemers"].append(naam)
        self.write_edities(data)

    def annuleren_editie(self, editie_id: str, naam: str, vandaag: date) -> None:
        data = self.read_edities()
        editie = self._vind_editie(data, editie_id)
        if naam not in editie["deelnemers"]:
            raise ValueError(f"'{naam}' is niet ingeschreven voor deze editie")
        eerste_datum = date.fromisoformat(editie["sessies"][0]["datum"])
        if (eerste_datum - vandaag).days < ANNULERING_DEADLINE_DAGEN:
            raise ValueError(
                f"Annuleren is niet meer mogelijk — deadline was "
                f"{ANNULERING_DEADLINE_DAGEN} dagen voor de eerste sessie"
            )
        editie["deelnemers"].remove(naam)
        self.write_edities(data)

    def get_edities_voor_medewerker(self, naam: str) -> list[dict]:
        data = self.read_edities()
        return [e for e in data.get("edities", []) if naam in e["deelnemers"]]

    def lijst_gebruikers(self) -> list[dict]:
        """Geeft lijst van {naam, profiel} gesorteerd op naam."""
        plannen = self.read_plannen()
        return sorted(
            [{"naam": k, "profiel": v.get("profiel", "")} for k, v in plannen.items()],
            key=lambda x: x["naam"].lower()
        )
