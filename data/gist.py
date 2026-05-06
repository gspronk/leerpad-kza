# data/gist.py
import json
import time
from github import Github

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

    def lijst_gebruikers(self) -> list[dict]:
        """Geeft lijst van {naam, profiel} gesorteerd op naam."""
        plannen = self.read_plannen()
        return sorted(
            [{"naam": k, "profiel": v.get("profiel", "")} for k, v in plannen.items()],
            key=lambda x: x["naam"].lower()
        )
