# Emailbevestiging via KZA Microsoft 365 SMTP

Bij inschrijving op een Sessie ontvangt de Medewerker een bevestigingsemail op het emailadres in zijn profiel. Dit verloopt via KZA's bestaande Microsoft 365 SMTP-server (smtp.office365.com).

We kozen niet voor een externe emaildienst (SendGrid, Mailgun) omdat KZA al beschikt over een Microsoft 365-omgeving met SMTP-toegang. Een externe dienst introduceert extra kosten, een API-sleutel als secret, en afhankelijkheid van een derde partij voor een bijkomende feature.

SMTP-credentials worden opgeslagen als Streamlit secrets (`SMTP_USER`, `SMTP_PASSWORD`), net als de bestaande GitHub-token. Emailverzending is fire-and-forget: een fout bij verzending blokkeert de inschrijving niet — de Inschrijving is al opgeslagen in `sessies.json`.

## Consequences

Medewerkers zonder emailadres in hun profiel ontvangen geen bevestiging. De app toont bij inschrijving een waarschuwing als er geen email bekend is, maar blokkeert de inschrijving niet. Email is aanvullend op de inschrijving, niet een vereiste ervoor.
