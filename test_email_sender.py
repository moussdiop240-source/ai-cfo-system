"""
Tests for email_sender.py.

Run with:
    pytest test_email_sender.py -v

Real SMTP credentials are never required — all network calls are mocked.
Set EMAIL_USERNAME / EMAIL_PASSWORD in .env or the test environment to test
EmailConfig.from_env() with real values (the send path is still mocked).
"""

import smtplib
from unittest.mock import MagicMock, call, patch

import pytest

from email_sender import EmailConfig, EmailSendError, send_email, send_lead_email


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_mock_smtp():
    """Return a mock SMTP instance that works as a context manager."""
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    return mock


@pytest.fixture
def cfg():
    return EmailConfig(
        host="smtp.example.com",
        port=587,
        username="sender@example.com",
        password="secret",
        sender="sender@example.com",
        use_tls=True,
    )


# ── EmailConfig.from_env ──────────────────────────────────────────────────────

def test_from_env_reads_all_vars(monkeypatch):
    monkeypatch.setenv("EMAIL_HOST", "smtp.custom.com")
    monkeypatch.setenv("EMAIL_PORT", "465")
    monkeypatch.setenv("EMAIL_USERNAME", "u@custom.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "pw")
    monkeypatch.setenv("EMAIL_FROM", "from@custom.com")
    monkeypatch.setenv("EMAIL_USE_TLS", "false")

    config = EmailConfig.from_env()

    assert config.host == "smtp.custom.com"
    assert config.port == 465
    assert config.username == "u@custom.com"
    assert config.password == "pw"
    assert config.sender == "from@custom.com"
    assert config.use_tls is False


def test_from_env_defaults(monkeypatch):
    monkeypatch.setenv("EMAIL_USERNAME", "u@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "pw")
    for key in ("EMAIL_HOST", "EMAIL_PORT", "EMAIL_FROM", "EMAIL_USE_TLS"):
        monkeypatch.delenv(key, raising=False)

    config = EmailConfig.from_env()

    assert config.host == "smtp.gmail.com"
    assert config.port == 587
    assert config.sender == "u@example.com"  # falls back to username
    assert config.use_tls is True


def test_from_env_missing_username_raises(monkeypatch):
    monkeypatch.delenv("EMAIL_USERNAME", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="EMAIL_USERNAME and EMAIL_PASSWORD must be set"):
        EmailConfig.from_env()


def test_from_env_missing_password_raises(monkeypatch):
    monkeypatch.setenv("EMAIL_USERNAME", "u@example.com")
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="EMAIL_USERNAME and EMAIL_PASSWORD must be set"):
        EmailConfig.from_env()


# ── send_email — happy path ───────────────────────────────────────────────────

def test_send_email_tls_success(cfg):
    mock_smtp = _make_mock_smtp()

    with patch("smtplib.SMTP", return_value=mock_smtp):
        send_email("to@example.com", "Hello", "Body text", cfg)

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with(cfg.username, cfg.password)
    mock_smtp.sendmail.assert_called_once()
    args = mock_smtp.sendmail.call_args
    assert args[0][0] == cfg.sender
    assert args[0][1] == ["to@example.com"]


def test_send_email_ssl_success():
    cfg_ssl = EmailConfig(
        host="smtp.example.com",
        port=465,
        username="u@example.com",
        password="pw",
        sender="u@example.com",
        use_tls=False,
    )
    mock_smtp = _make_mock_smtp()

    with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
        send_email("to@example.com", "Subject", "Body", cfg_ssl)

    mock_smtp.login.assert_called_once_with(cfg_ssl.username, cfg_ssl.password)
    mock_smtp.sendmail.assert_called_once()


# ── send_email — error cases ──────────────────────────────────────────────────

def test_send_email_auth_error_raises(cfg):
    mock_smtp = _make_mock_smtp()
    mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

    with patch("smtplib.SMTP", return_value=mock_smtp):
        with pytest.raises(EmailSendError, match="Authentication failed"):
            send_email("to@example.com", "S", "B", cfg)


def test_send_email_connect_error_raises(cfg):
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, b"Unavailable")):
        with pytest.raises(EmailSendError, match="Connection failed"):
            send_email("to@example.com", "S", "B", cfg)


def test_send_email_recipient_refused_raises(cfg):
    mock_smtp = _make_mock_smtp()
    mock_smtp.sendmail.side_effect = smtplib.SMTPRecipientsRefused({"to@example.com": (550, b"No such user")})

    with patch("smtplib.SMTP", return_value=mock_smtp):
        with pytest.raises(EmailSendError, match="Recipient refused"):
            send_email("to@example.com", "S", "B", cfg)


def test_send_email_network_error_raises(cfg):
    with patch("smtplib.SMTP", side_effect=OSError("Network unreachable")):
        with pytest.raises(EmailSendError, match="Network error"):
            send_email("to@example.com", "S", "B", cfg)


# ── send_lead_email ───────────────────────────────────────────────────────────

def test_send_lead_email_parses_subject_and_body(tmp_path, cfg):
    import email as _email

    email_file = tmp_path / "email_acme.txt"
    email_file.write_text(
        "Subject: Your site needs a better headline\n\nHi Acme,\n\nHere's a rewrite.",
        encoding="utf-8",
    )
    mock_smtp = _make_mock_smtp()

    with patch("smtplib.SMTP", return_value=mock_smtp):
        send_lead_email("prospect@acme.com", str(email_file), cfg)

    raw_message = mock_smtp.sendmail.call_args[0][2]
    parsed = _email.message_from_string(raw_message)
    assert parsed["Subject"] == "Your site needs a better headline"
    assert parsed["To"] == "prospect@acme.com"

    body = parsed.get_payload(0).get_payload(decode=True).decode("utf-8")
    assert "Hi Acme" in body


def test_send_lead_email_fallback_subject(tmp_path, cfg):
    email_file = tmp_path / "email_roofing_co.txt"
    email_file.write_text("No subject line here.\nJust body text.", encoding="utf-8")
    mock_smtp = _make_mock_smtp()

    with patch("smtplib.SMTP", return_value=mock_smtp):
        send_lead_email("to@example.com", str(email_file), cfg)

    raw_message = mock_smtp.sendmail.call_args[0][2]
    # Fallback subject is derived from filename
    assert "Email Roofing Co" in raw_message


def test_send_lead_email_missing_file_raises(cfg):
    with pytest.raises(FileNotFoundError, match="Email file not found"):
        send_lead_email("to@example.com", "/no/such/file.txt", cfg)
