from data.milestones import bereken_mijlpalen, hoogste_mijlpaal

DATA = {
    "blokken": {
        "engineer": [
            {
                "sectie": "Basis",
                "items": [
                    {"id": "qa-basis", "naam": "QA Basis", "kern": True},
                    {"id": "qa-tools", "naam": "QA Tools", "kern": True},
                    {"id": "qa-extra", "naam": "QA Extra", "kern": False},
                ],
            }
        ]
    },
    "fases": {
        "engineer": [
            {"num": 1, "naam": "Fundament", "items": ["qa-basis", "qa-tools"]},
            {"num": 2, "naam": "Verdieping", "items": ["qa-extra"]},
        ]
    },
}

PLAN_LEEG = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools"],
    "statussen": {},
}

PLAN_EEN_AFGEROND = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond"},
}

PLAN_FASE1_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond"},
}

PLAN_KERN_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond", "qa-extra": "gepland"},
}

PLAN_ALLES_VOLTOOID = {
    "profiel": "engineer",
    "geselecteerd": ["qa-basis", "qa-tools", "qa-extra"],
    "statussen": {"qa-basis": "afgerond", "qa-tools": "afgerond", "qa-extra": "afgerond"},
}


def test_geen_mijlpalen_als_niets_afgerond():
    assert bereken_mijlpalen(PLAN_LEEG, DATA) == []


def test_eerste_cursus_bij_een_afgerond():
    ids = [m.id for m in bereken_mijlpalen(PLAN_EEN_AFGEROND, DATA)]
    assert "eerste_cursus" in ids


def test_fase1_voltooid_bevat_beide_mijlpalen():
    ids = [m.id for m in bereken_mijlpalen(PLAN_FASE1_VOLTOOID, DATA)]
    assert "eerste_cursus" in ids
    assert "fase_1_voltooid" in ids


def test_fase2_niet_voltooid_als_item_ontbreekt():
    ids = [m.id for m in bereken_mijlpalen(PLAN_FASE1_VOLTOOID, DATA)]
    assert "fase_2_voltooid" not in ids


def test_alle_kern_voltooid():
    ids = [m.id for m in bereken_mijlpalen(PLAN_KERN_VOLTOOID, DATA)]
    assert "alle_kern" in ids


def test_leerplan_volledig():
    ids = [m.id for m in bereken_mijlpalen(PLAN_ALLES_VOLTOOID, DATA)]
    assert "leerplan_volledig" in ids


def test_gesorteerd_op_prioriteit_laag_naar_hoog():
    resultaat = bereken_mijlpalen(PLAN_ALLES_VOLTOOID, DATA)
    prio = [m.prioriteit for m in resultaat]
    assert prio == sorted(prio)


def test_hoogste_mijlpaal_geeft_leerplan_volledig():
    m = hoogste_mijlpaal(PLAN_ALLES_VOLTOOID, DATA)
    assert m.id == "leerplan_volledig"


def test_hoogste_mijlpaal_none_als_niets_afgerond():
    assert hoogste_mijlpaal(PLAN_LEEG, DATA) is None


def test_fase_zonder_items_niet_voltooid():
    data_leeg = {
        **DATA,
        "fases": {"engineer": [{"num": 1, "naam": "Leeg", "items": []}]},
    }
    ids = [m.id for m in bereken_mijlpalen(PLAN_EEN_AFGEROND, data_leeg)]
    assert "fase_1_voltooid" not in ids
