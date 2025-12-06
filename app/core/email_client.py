# app/core/email_client.py
from __future__ import annotations

"""
Email client utilities for Amoura backend.

Responsibilities:
  - Read SMTP configuration from environment variables.
  - Provide a single send_email(...) function for services to use.
  - Support both TLS (STARTTLS) and SSL connections.

Typical .env configuration (Gmail example with App Password):

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=465
    SMTP_USERNAME=amourapastry@gmail.com
    SMTP_PASSWORD=zohneeplxleeuxxl
    SMTP_FROM_EMAIL=amourapastry@gmail.com
    SMTP_FROM_NAME=Amoura Pastry
    SMTP_USE_TLS=false
    SMTP_USE_SSL=true
"""

import os
import smtplib
from email.message import EmailMessage


def _get_bool_env(name: str, default: bool = False) -> bool:
    """
    Read a boolean env var.

    Accepted truthy values (case-insensitive):
      - "1", "true", "yes", "y"

    Everything else is treated as False.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


# ---------------------------------------------------------------------------
# Configuration: read once at import time
# ---------------------------------------------------------------------------

SMTP_HOST: str | None = os.getenv("SMTP_HOST")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")

# Fallback: if FROM_EMAIL is not set, default to username
SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME or "")

# Human-readable sender name, shown in email clients
SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Amoura Cakes")

# Connection mode flags
SMTP_USE_TLS: bool = _get_bool_env("SMTP_USE_TLS", default=True)
SMTP_USE_SSL: bool = _get_bool_env("SMTP_USE_SSL", default=False)


def _create_smtp_client() -> smtplib.SMTP:
    """
    Create and return an SMTP client configured for TLS or SSL.

    Priority:
      - If SMTP_USE_SSL is True → use smtplib.SMTP_SSL (e.g., Gmail on 465).
      - Else → use smtplib.SMTP + optional STARTTLS if SMTP_USE_TLS is True.

    NOTE:
      - You should NOT enable both TLS and SSL at the same time.
      - Typical configs:
          * SSL: SMTP_PORT=465, SMTP_USE_SSL=true,  SMTP_USE_TLS=false
          * TLS: SMTP_PORT=587, SMTP_USE_SSL=false, SMTP_USE_TLS=true
    """
    if not SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured. Please set it in .env.")

    if SMTP_USE_SSL:
        # Direct SSL connection (commonly port 465)
        server: smtplib.SMTP = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
    else:
        # Plain connection, optionally upgraded via STARTTLS (commonly port 587)
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        if SMTP_USE_TLS:
            server.starttls()

    return server


def send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    """
    Send an email to a single recipient.

    Parameters
    ----------
    to_email:
        Recipient email address.
    subject:
        Email subject line.
    text_body:
        Plain-text body (required, used as the fallback for clients that
        do not support HTML).
    html_body:
        Optional HTML body; if provided, is sent as an alternative part.

    Raises
    ------
    RuntimeError:
        If required SMTP configuration is missing.
    smtplib.SMTPException:
        If the underlying SMTP connection or send fails.

    Usage in services:
        from app.core.email_client import send_email

        send_email(
            to_email=user.email,
            subject="[Amoura] Your order is confirmed",
            text_body="Plain text version...",
            html_body="<p>HTML version...</p>",
        )
    """
    if not (SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD):
        raise RuntimeError(
            "SMTP is not configured correctly. "
            "Please set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD in .env."
        )

    # Build email message
    msg = EmailMessage()

    from_header = (
        f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        if SMTP_FROM_EMAIL
        else SMTP_USERNAME
    )
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Subject"] = subject

    # Always add a plain-text part
    msg.set_content(text_body)

    # Optional HTML alternative
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    # Open SMTP connection and send
    server = _create_smtp_client()
    try:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)  # type: ignore[arg-type]
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            # Ignore errors on quit; connection is being torn down anyway.
            pass
