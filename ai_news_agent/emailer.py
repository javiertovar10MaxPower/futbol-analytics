import logging
import os
import smtplib
import time
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587  # STARTTLS — Microsoft no longer supports SMTPS on 465 for personal accounts


def send(html_body: str, today: date) -> None:
    sender = os.environ["OUTLOOK_EMAIL"]
    password = os.environ["OUTLOOK_APP_PASSWORD"]
    recipient = os.environ["RECIPIENT_EMAIL"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Resumen semanal IA — {today.isoformat()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    delays = [0, 2, 4, 8]
    last_error: Exception | None = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            logger.info("SMTP attempt %d/%d to %s", attempt, len(delays), recipient)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(sender, password)
                smtp.send_message(msg)
            logger.info("Email sent successfully to %s", recipient)
            return
        except (smtplib.SMTPException, OSError) as e:
            logger.warning("SMTP attempt %d failed: %s", attempt, e)
            last_error = e

    raise RuntimeError(f"Failed to send email after {len(delays)} attempts") from last_error
