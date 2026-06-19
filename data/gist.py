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
        self._sessies_cache: dict | None = None
        self._sessies_cache_time: float = 0
        self._cache_ttl: float = CACHE_TTL

    def _get_gist(self):
        if self._gist is None:
            self._gist = self._gh.get_gist(self._gist_id)
        return self._gist

    def _read_file(self, filename: str) -> dict:
        gist = self._gh.get_gist(self._gist_id)  # altijd verse gist voor reads
        self._gist = gist
        content = gist.files[filename].content
        return json.loads(content)

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

    # ── sessies ────────────────────────────────────────────────

    def read_sessies(self) -> dict:
        now = time.time()
        if self._sessies_cache is not None and (now - self._sessies_cache_time) < self._cache_ttl:
            return self._sessies_cache
        try:
            self._sessies_cache = self._read_file("sessies.json")
        except (KeyError, AttributeError, TypeError):
            self._sessies_cache = {"sessies": []}
        self._sessies_cache_time = time.time()
        return self._sessies_cache

    def write_sessies(self, data: dict) -> None:
        self._write_file("sessies.json", data)
        self._sessies_cache = None
        self._sessies_cache_time = 0

    def _vind_sessie(self, sessies: dict, sessie_id: str) -> dict:
        for s in sessies.get("sessies", []):
            if s["id"] == sessie_id:
                return s
        raise ValueError(f"Sessie '{sessie_id}' niet gevonden")

    def inschrijven(self, sessie_id: str, naam: str) -> None:
        sessies = self.read_sessies()
        sessie = self._vind_sessie(sessies, sessie_id)
        if naam in sessie["deelnemers"]:
            raise ValueError(f"'{naam}' is al ingeschreven voor deze sessie")
        if len(sessie["deelnemers"]) >= sessie["max_deelnemers"]:
            raise ValueError("Sessie is vol")
        sessie["deelnemers"].append(naam)
        self.write_sessies(sessies)

    def annuleren(self, sessie_id: str, naam: str, vandaag: date) -> None:
        sessies = self.read_sessies()
        sessie = self._vind_sessie(sessies, sessie_id)
        if naam not in sessie["deelnemers"]:
            raise ValueError(f"'{naam}' is niet ingeschreven voor deze sessie")
        sessiedatum = date.fromisoformat(sessie["datum"])
        if (sessiedatum - vandaag).days < ANNULERING_DEADLINE_DAGEN:
            raise ValueError(
                f"Annuleren is niet meer mogelijk — deadline was "
                f"{ANNULERING_DEADLINE_DAGEN} dagen voor de sessie"
            )
        sessie["deelnemers"].remove(naam)
        self.write_sessies(sessies)

    def get_sessies_voor_medewerker(self, naam: str) -> list[dict]:
        sessies = self.read_sessies()
        return [s for s in sessies.get("sessies", []) if naam in s["deelnemers"]]

    def lijst_gebruikers(self) -> list[dict]:
        """Geeft lijst van {naam, profiel} gesorteerd op naam."""
        plannen = self.read_plannen()
        return sorted(
            [{"naam": k, "profiel": v.get("profiel", "")} for k, v in plannen.items()],
            key=lambda x: x["naam"].lower()
        )
