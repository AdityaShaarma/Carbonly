"""Email provider stub (DEV logs; PROD warns if unconfigured)."""
import logging
import os
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("carbonly.email")
settings = get_settings()


def send_email(to: str, subject: str, body: str) -> None:
    if settings.env in {"local", "development"}:
        logger.info("DEV EMAIL to=%s subject=%s body=%s", to, subject, body)
        return

    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")

    if not smtp_host or not smtp_user or not smtp_pass or not email_from:
        logger.warning("Email not sent: SMTP not configured")
        return

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, 587) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
