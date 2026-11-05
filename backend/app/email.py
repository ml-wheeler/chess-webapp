import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_account_link(recipient: str, subject: str, purpose: str, token: str) -> None:
    url = f"{settings.frontend_url}/{purpose}?token={token}"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(f"Use this link to continue: {url}\n\nIf you did not request this, ignore this email.")

    if not settings.smtp_host:
        if settings.app_env == "development":
            logger.warning("Email delivery is not configured. Development link for %s: %s", recipient, url)
            return
        raise RuntimeError("SMTP_HOST must be configured outside development")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
