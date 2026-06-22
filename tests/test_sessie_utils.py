# tests/test_sessie_utils.py
from unittest.mock import patch, MagicMock
from data.sessie_utils import genereer_ics_editie, stuur_bevestigingsmail

EDITIE = {
    "id": "edit-qa2-cloud-202607",
    "cursus_id": "qa2-cloud",
    "naam": "Editie juli 2026",
    "max_deelnemers": 12,
    "deelnemers": ["Gerson"],
    "sessies": [
        {"datum": "2026-07-15", "tijd": "09:00", "locatie": "KZA kantoor"},
        {"datum": "2026-07-16", "tijd": "10:00", "locatie": "Klantlocatie Utrecht"},
    ],
}

EDITIE_ENKEL = {
    "id": "edit-qa2-cloud-202608",
    "cursus_id": "qa2-cloud",
    "naam": "Editie augustus 2026",
    "max_deelnemers": 12,
    "deelnemers": ["Gerson"],
    "sessies": [
        {"datum": "2026-08-01", "tijd": "09:00", "locatie": "KZA kantoor"},
    ],
}


def test_genereer_ics_editie_bevat_verplichte_velden():
    ics = genereer_ics_editie(EDITIE, "Introductie Cloud & Containers")
    assert "BEGIN:VCALENDAR" in ics
    assert "END:VCALENDAR" in ics
    assert ics.count("BEGIN:VEVENT") == 2
    assert ics.count("END:VEVENT") == 2
    assert "SUMMARY:Introductie Cloud & Containers" in ics


def test_genereer_ics_editie_eerste_sessie_dtstart():
    ics = genereer_ics_editie(EDITIE, "Introductie Cloud")
    assert "DTSTART;TZID=Europe/Amsterdam:20260715T090000" in ics
    assert "DTEND;TZID=Europe/Amsterdam:20260715T170000" in ics


def test_genereer_ics_editie_tweede_sessie_dtstart():
    ics = genereer_ics_editie(EDITIE, "Introductie Cloud")
    assert "DTSTART;TZID=Europe/Amsterdam:20260716T100000" in ics
    assert "DTEND;TZID=Europe/Amsterdam:20260716T180000" in ics


def test_genereer_ics_editie_locaties():
    ics = genereer_ics_editie(EDITIE, "Introductie Cloud")
    assert "LOCATION:KZA kantoor" in ics
    assert "LOCATION:Klantlocatie Utrecht" in ics


def test_genereer_ics_editie_enkelvoudig():
    ics = genereer_ics_editie(EDITIE_ENKEL, "Introductie Cloud")
    assert ics.count("BEGIN:VEVENT") == 1


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
        stuur_bevestigingsmail("Gerson", "gerson@kza.nl", EDITIE, "Introductie Cloud", smtp_config)
        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args[0]
        assert args[1] == "gerson@kza.nl"


def test_stuur_bevestigingsmail_gooit_bij_smtp_fout():
    import pytest
    smtp_config = {"host": "smtp.office365.com", "port": 587, "user": "x", "password": "y"}
    with patch("smtplib.SMTP", side_effect=Exception("verbinding geweigerd")):
        with pytest.raises(Exception, match="verbinding geweigerd"):
            stuur_bevestigingsmail("Gerson", "gerson@kza.nl", EDITIE, "Introductie Cloud", smtp_config)
