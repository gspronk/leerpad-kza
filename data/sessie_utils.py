import smtplib
import textwrap
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def genereer_ics_editie(editie: dict, cursus_naam: str) -> str:
    vevents = []
    for i, sessie in enumerate(editie["sessies"]):
        datum = sessie["datum"].replace("-", "")
        tijd = sessie["tijd"].replace(":", "") + "00"
        dtstart = f"{datum}T{tijd}"
        vevents.append(
            f"BEGIN:VEVENT\r\n"
            f"UID:{editie['id']}-{i}@kza.nl\r\n"
            f"DTSTART:{dtstart}\r\n"
            f"SUMMARY:{cursus_naam}\r\n"
            f"LOCATION:{sessie.get('locatie', '')}\r\n"
            f"DESCRIPTION:KZA cursus - {cursus_naam}\r\n"
            f"END:VEVENT"
        )
    events_str = "\r\n".join(vevents)
    return (
        f"BEGIN:VCALENDAR\r\n"
        f"VERSION:2.0\r\n"
        f"PRODID:-//KZA Leerpad//NL\r\n"
        f"{events_str}\r\n"
        f"END:VCALENDAR\r\n"
    )


def stuur_bevestigingsmail(
    naam: str,
    email: str,
    editie: dict,
    cursus_naam: str,
    smtp_config: dict,
) -> None:
    try:
        sessie_regels = "\n".join(
            f"  - {s['datum']} om {s.get('tijd', '')} · {s.get('locatie', '')}"
            for s in editie.get("sessies", [])
        )
        msg = MIMEMultipart()
        msg["From"] = smtp_config["user"]
        msg["To"] = email
        msg["Subject"] = f"Inschrijving bevestigd: {cursus_naam}"
        body = (
            f"Hoi {naam},\n\n"
            f"Je bent ingeschreven voor '{cursus_naam}' ({editie.get('naam', '')}).\n\n"
            f"Bijeenkomsten:\n{sessie_regels}\n\n"
            f"Tot dan!\nKZA Leerpad"
        )
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.sendmail(smtp_config["user"], email, msg.as_string())
    except Exception:
        pass
