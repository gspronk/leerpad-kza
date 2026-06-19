# KZA Leerpad

Een leerpadbeheer-app voor KZA-medewerkers. Medewerkers kiezen een profiel, selecteren cursussen, volgen hun voortgang en schrijven zich in op geplande sessies.

## Language

### Catalogus

**Cursus**:
Een opleidingsonderdeel in de catalogus, gedefinieerd één keer en herbruikbaar. Een Cursus heeft een id, naam, beschrijving, tags en duur.
_Avoid_: Training, module, les

**Profiel**:
Een leertraject dat bepaalt welke cursussen kernvereisten zijn. Er zijn zes profielen: engineer, enabler, academy, maatwerk, security, ai.
_Avoid_: Rol, track, pad

**Fase**:
Een opeenvolgende stap in een Profiel, bestaande uit een geordende set Cursussen.
_Avoid_: Niveau, stap, stage

### Planning

**Sessie**:
Een geplande uitvoering van een Cursus op een specifieke datum met een maximaal aantal plaatsen. Een Sessie is tijdelijk — ze wordt aangemaakt door een beheerder en vervalt na de datum.
_Avoid_: Cursusmoment, training, evenement

**Capaciteit**:
Het maximale aantal Inschrijvingen dat een Sessie kan bevatten. Wanneer het aantal Inschrijvingen de Capaciteit bereikt, is de Sessie gesloten voor nieuwe Inschrijvingen.
_Avoid_: Maximumaantal, plaatsen, seats

### Deelname

**Medewerker**:
Een KZA-medewerker die de app gebruikt. Heeft een naam, een Profiel, een Leerplan en optioneel een emailadres.
_Avoid_: Gebruiker, deelnemer, cursist

**Leerplan**:
De persoonlijke selectie van Cursussen en hun voortgangsstatussen voor één Medewerker.
_Avoid_: Plan, leerpad, portfolio

**Inschrijving**:
De koppeling tussen een Medewerker en een Sessie. Ontstaat wanneer een Medewerker zich aanmeldt; verdwijnt bij Annulering.
_Avoid_: Aanmelding, registratie, boeking

**Annulering**:
Het intrekken van een Inschrijving door de Medewerker zelf. Alleen mogelijk vóór de Annuleringsdeadline.
_Avoid_: Uitschrijving, afmelding, cancellation

**Annuleringsdeadline**:
Het laatste moment waarop een Medewerker een Inschrijving kan annuleren: zeven dagen vóór de Sessiedatum.
_Avoid_: Annuleringstermijn, deadline
