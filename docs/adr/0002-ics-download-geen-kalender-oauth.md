# .ics download in plaats van kalenderintegratie via OAuth

Na inschrijving op een Sessie kan een Medewerker een `.ics`-bestand downloaden om de afspraak aan zijn eigen kalender toe te voegen. Er is geen directe integratie met Microsoft 365 of Google Calendar.

Een OAuth-koppeling met Microsoft 365 (Graph API) zou een automatische agenda-uitnodiging kunnen sturen, maar vereist een geregistreerde Azure-app, redirect-URI's, en token-beheer — infrastructuur die niet bestaat in de huidige Streamlit + Gist architectuur. Streamlit is een stateless single-page app; er is geen server-side scheduler die uitnodigingen kan versturen bij inschrijving.

Een `.ics`-download werkt met elk kalendersysteem (Outlook, Google, Apple), vereist geen credentials, en kan volledig client-side worden gegenereerd als een `text/calendar` download-knop. De trade-off is dat de afspraak niet automatisch verschijnt — de Medewerker moet de download zelf importeren.
