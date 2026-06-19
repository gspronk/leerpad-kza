# Sessies en inschrijvingen in een apart sessies.json bestand

De app gebruikt GitHub Gist als database met twee bestaande bestanden: `cursussen.json` (catalogus) en `plannen.json` (voortgang per Medewerker). Voor Sessies en Inschrijvingen voegen we een derde bestand toe: `sessies.json`.

We kozen niet voor uitbreiding van `cursussen.json` omdat dat bestand de *tijdloze catalogus* beschrijft — wat een Cursus is, niet wanneer die plaatsvindt. Sessies zijn vluchtige planningsdata die groeien en vervallen; ze horen conceptueel en praktisch in een apart bestand. Mixen zou `cursussen.json` onbeperkt laten groeien met historische sessiedata.

We kozen niet voor opslag in `plannen.json` (per Medewerker) omdat capaciteitscontrole een actuele deelnemerslijst *per Sessie* vereist. Om te weten of een Sessie vol is, moet je alle plannen scannen — dat is O(n) over alle Medewerkers bij elke paginaweergave. Door `deelnemers` bij de Sessie op te slaan, is capaciteitscontrole een directe lookup.

## Datastructuur sessies.json

```json
{
  "sessies": [
    {
      "id": "sess-qa2-cloud-20260715",
      "cursus_id": "qa2-cloud",
      "datum": "2026-07-15",
      "tijd": "09:00",
      "locatie": "KZA kantoor",
      "max_deelnemers": 12,
      "deelnemers": ["Gerson", "Anna"]
    }
  ]
}
```

## Consequences

Een Inschrijving wordt uitsluitend bijgehouden in `sessies.json[].deelnemers`. Plannen.json bevat geen inschrijvingen — een Medewerker's actieve inschrijvingen worden opgehaald door `sessies.json` te filteren op naam. Dit is consistent bij schrijfoperaties: inschrijven of annuleren raakt altijd maar één bestand.
