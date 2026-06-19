# Editie-model: cursus bestaat uit één of meer sessies

Het bestaande model kende één concept: een `sessie` — een enkelvoudige geplande uitvoering van een cursus op een datum. Dit maakte het onmogelijk om meerdaagse cursussen te modelleren waarbij deelnemers zich inschrijven voor de volledige reeks bijeenkomsten.

We vervangen het sessie-model door een **editie-model** met twee niveaus:

- **Editie** — de inschrijfbare eenheid: één geplande uitvoering van een cursus, bestaande uit 1 of meer bijeenkomsten.
- **Sessie** (binnen een editie) — een individuele bijeenkomst op een specifieke datum, tijd en locatie.

Inschrijving vindt plaats op editieniveau, niet op sessieniveau. Deelnemers committeren zich daarmee aan alle bijeenkomsten binnen de editie.

## Motivatie

Sommige cursussen bestaan uit meerdere aaneengesloten bijeenkomsten op verschillende datums en/of locaties (bijv. dag 1 op kantoor, dag 2 op klantlocatie). Het oude model kon dit niet uitdrukken — elke sessie was een zelfstandige eenheid zonder relatie tot andere sessies van dezelfde cursusuitvoering.

We kozen niet voor een eenvoudige `parent_id`-koppeling tussen bestaande sessies, omdat dat het inschrijvingslogic ingewikkeld maakt (je zou op alle child-sessies tegelijk moeten inschrijven). Een expliciete editie-laag maakt inschrijving, capaciteitsbeheer en weergave eenduidig.

## Verwijderingsregel

Een editie mag worden verwijderd zolang er **minder dan 5 deelnemers** zijn ingeschreven (0–4). Bij 5 of meer ingeschreven deelnemers is verwijdering geblokkeerd. Er wordt geen automatische notificatie verstuurd bij verwijdering (e-mail is buiten scope).

## Migratie

Het bestaande `sessies.json` wordt geleegd bij introductie van dit model. Bestaande sessies worden niet gemigreerd — beheerders voeren edities opnieuw in via de beheerpagina.

## Datastructuur sessies.json (nieuw)

```json
{
  "edities": [
    {
      "id": "edit-selenium-advanced-202603",
      "cursus_id": "selenium-advanced",
      "naam": "Editie maart 2026",
      "max_deelnemers": 12,
      "deelnemers": ["Gerson", "Anna"],
      "sessies": [
        { "datum": "2026-03-03", "tijd": "09:00", "locatie": "KZA kantoor" },
        { "datum": "2026-03-04", "tijd": "09:00", "locatie": "Klantlocatie Utrecht" },
        { "datum": "2026-03-05", "tijd": "09:00", "locatie": "KZA kantoor" }
      ]
    }
  ]
}
```

## Velden editie

| Veld | Type | Toelichting |
|---|---|---|
| `id` | string | `edit-{cursus_id}-{YYYYMM}` van eerste sessie |
| `cursus_id` | string | Verwijzing naar catalogus; niet wijzigbaar na aanmaak |
| `naam` | string | Default `"Editie {maand} {jaar}"`, aanpasbaar |
| `max_deelnemers` | int | Capaciteit voor de hele editie |
| `deelnemers` | string[] | Namen van ingeschreven medewerkers |
| `sessies` | object[] | Lijst van bijeenkomsten (datum, tijd, locatie) |

## Weergave in kalender

De kalender toont één kaart per editie. De individuele sessies worden opgesomd als een compact lijstje (datum · tijd · locatie). Er is één inschrijfknop per editie.

## Consequences

- `GistClient` krijgt nieuwe methoden: `read_edities`, `write_edities`, `inschrijven_editie`, `annuleren_editie`.
- De sleutel in `sessies.json` wijzigt van `"sessies"` naar `"edities"`.
- `views/beheer.py` en `views/kalender.py` worden volledig herschreven voor het nieuwe model.
- ADR-0001 vervalt gedeeltelijk: de bestandsnaam `sessies.json` blijft, maar de interne structuur wijzigt ingrijpend.
