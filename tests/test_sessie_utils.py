# tests/test_sessie_utils.py
from unittest.mock import patch, MagicMock
from data.sessie_utils import genereer_ics, stuur_bevestigingsmail

SESSIE = {
    "id": "sess-qa2-cloud-20260715",
    "cursus_id": "qa2-cloud",
    "datum": "2026-07-15",
    "tijd": "09:00",
    "locatie": "KZA kantoor",
    "max_deelnemers": 12,
    "deelnemers": ["Gerson"],
}


def test_genereer_ics_bevat_verplichte_velden():
    ics = genereer_ics(SESSIE, "Introductie Cloud & Containers")
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "END:VEVENT" in ics
    assert "END:VCALENDAR" in ics
    assert "DTSTART" in ics
    assert "SUMMARY:Introductie Cloud & Containers" in ics
    assert "LOCATION:KZA kantoor" in ics


def test_genereer_ics_datum_formaat():
    ics = genereer_ics(SESSIE, "Introductie Cloud")
    assert "DTSTART:20260715T090000" in ics


def test_stuur_bevestigingsmail_verstuurt_via_smtp():
    smtp_config = {
        "host": "smtp.office365.com",
        "port": 587,
        "user": "noreply@kza.nl",
        "password": "secret",
    }
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        stuur_bevestigingsmail("Gerson", "gerson@kza.nl", SESSIE, "Introductie Cloud", smtp_config)
        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args[0]
        assert args[1] == "gerson@kza.nl"


def test_stuur_bevestigingsmail_slikt_smtp_fout():
    smtp_config = {"host": "smtp.office365.com", "port": 587, "user": "x", "password": "y"}
    with patch("smtplib.SMTP", side_effect=Exception("verbinding geweigerd")):
        # mag geen exception gooien
        stuur_bevestigingsmail("Gerson", "gerson@kza.nl", SESSIE, "Introductie Cloud", smtp_config)
