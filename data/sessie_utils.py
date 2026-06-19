import smtplib
import textwrap
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def genereer_ics(sessie: dict, cursus_naam: str) -> str:
    datum = sessie["datum"].replace("-", "")
    tijd = sessie["tijd"].replace(":", "") + "00"
    dtstart = f"{datum}T{tijd}"
    return textwrap.dedent(f"""\
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:-//KZA Leerpad//NL
        BEGIN:VEVENT
        UID:{sessie["id"]}@kza.nl
        DTSTART:{dtstart}
        SUMMARY:{cursus_naam}
        LOCATION:{sessie.get("locatie", "")}
        DESCRIPTION:KZA cursus - {cursus_naam}
        END:VEVENT
        END:VCALENDAR
    """)


def stuur_bevestigingsmail(
    naam: str,
    email: str,
    sessie: dict,
    cursus_naam: str,
    smtp_config: dict,
) -> None:
    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_config["user"]
        msg["To"] = email
        msg["Subject"] = f"Inschrijving bevestigd: {cursus_naam}"
        body = (
            f"Hoi {naam},\n\n"
            f"Je bent ingeschreven voor '{cursus_naam}'.\n"
            f"Datum: {sessie['datum']} om {sessie.get('tijd', '')}\n"
            f"Locatie: {sessie.get('locatie', '')}\n\n"
            f"Tot dan!\nKZA Leerpad"
        )
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.sendmail(smtp_config["user"], email, msg.as_string())
    except Exception:
        pass
