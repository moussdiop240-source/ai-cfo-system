"""
SMTP email sending module for the AI Lead Prospector.
Configuration is loaded from environment variables (via .env file).
"""

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when an email fails to send."""


@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "EmailConfig":
        username = os.getenv("EMAIL_USERNAME", "")
        password = os.getenv("EMAIL_PASSWORD", "")

        if not username or not password:
            raise ValueError("EMAIL_USERNAME and EMAIL_PASSWORD must be set in environment")

        return cls(
            host=os.getenv("EMAIL_HOST", "smtp.gmail.com"),
            port=int(os.getenv("EMAIL_PORT", "587")),
            username=username,
            password=password,
            sender=os.getenv("EMAIL_FROM", username),
            use_tls=os.getenv("EMAIL_USE_TLS", "true").lower() == "true",
        )


def send_email(
    to: str,
    subject: str,
    body: str,
    config: EmailConfig | None = None,
) -> None:
    """Send a plain-text email. Raises EmailSendError on failure."""
    if config is None:
        config = EmailConfig.from_env()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.sender
    msg["To"] = to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    logger.info("Sending email to %s | subject: %r", to, subject)

    try:
        if config.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(config.host, config.port) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.login(config.username, config.password)
                smtp.sendmail(config.sender, [to], msg.as_string())
        else:
            with smtplib.SMTP_SSL(config.host, config.port) as smtp:
                smtp.login(config.username, config.password)
                smtp.sendmail(config.sender, [to], msg.as_string())

    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP authentication failed for %s: %s", config.username, exc)
        raise EmailSendError(f"Authentication failed: {exc}") from exc
    except smtplib.SMTPConnectError as exc:
        logger.error("Could not connect to %s:%s — %s", config.host, config.port, exc)
        raise EmailSendError(f"Connection failed: {exc}") from exc
    except smtplib.SMTPRecipientsRefused as exc:
        logger.error("Recipient refused by server: %s — %s", to, exc)
        raise EmailSendError(f"Recipient refused: {exc}") from exc
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending to %s: %s", to, exc)
        raise EmailSendError(f"SMTP error: {exc}") from exc
    except OSError as exc:
        logger.error("Network error sending to %s: %s", to, exc)
        raise EmailSendError(f"Network error: {exc}") from exc

    logger.info("Email delivered to %s", to)


def send_lead_email(
    to: str,
    email_file: str,
    config: EmailConfig | None = None,
) -> None:
    """Parse a saved lead email file and send it.

    Email files follow the format written by main.py:
        Subject: <subject line>

        <body...>
    """
    path = Path(email_file)
    if not path.exists():
        raise FileNotFoundError(f"Email file not found: {email_file}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    subject = ""
    body_start = 0
    if lines and lines[0].startswith("Subject: "):
        subject = lines[0].removeprefix("Subject: ").strip()
        body_start = 2 if len(lines) > 1 and not lines[1].strip() else 1

    body = "\n".join(lines[body_start:]).strip()

    if not subject:
        subject = path.stem.replace("_", " ").title()

    logger.info("Loaded email from %s", email_file)
    send_email(to, subject, body, config)
