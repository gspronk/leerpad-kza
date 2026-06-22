# Centrale definitie van alle zes leerprofielen.
# Importeer PROFIEL_META, PROFIEL_LABELS of PROFIEL_KLEUREN vanuit dit bestand.
PROFIEL_META: dict[str, dict] = {
    "engineer": {"label": "QA Engineer", "kleur": "#0072B8", "icon": "⚙️"},
    "enabler":  {"label": "QA Enabler",  "kleur": "#E5007D", "icon": "🎓"},
    "academy":  {"label": "KZAcademy",   "kleur": "#F0A500", "icon": "📚"},
    "maatwerk": {"label": "Op maat",     "kleur": "#A371F7", "icon": "✨"},
    "security": {"label": "Security",    "kleur": "#FF6B35", "icon": "🔒"},
    "ai":       {"label": "AI",          "kleur": "#10B981", "icon": "🤖"},
}

PROFIEL_LABELS: dict[str, str] = {k: v["label"] for k, v in PROFIEL_META.items()}
PROFIEL_KLEUREN: dict[str, str] = {k: v["kleur"] for k, v in PROFIEL_META.items()}
