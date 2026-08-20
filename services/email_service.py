"""Password-reset email sending.

Real sending happens via the Resend HTTPS API (using httpx, already a
project dependency) -- not SMTP. Railway blocks all outbound SMTP
(ports 25/465/587) on the Hobby plan, so no SMTP provider works here
regardless of credentials or host; Resend's API runs over HTTPS (443),
which stays open on every plan. Without RESEND_API_KEY/EMAIL_FROM
configured, the reset link is logged instead so local dev needs zero
env vars and MAC25AI can still relay a link manually (e.g. over
WhatsApp) from the Railway log viewer.
"""

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class EmailConfig:
    api_key: str
    from_address: str


def get_email_config() -> EmailConfig | None:
    api_key = os.environ.get("RESEND_API_KEY")
    from_address = os.environ.get("EMAIL_FROM")
    if not api_key or not from_address:
        return None
    return EmailConfig(api_key=api_key, from_address=from_address)


def send_password_reset_email(business_name: str, to_email: str, reset_url: str) -> bool:
    """Send the reset link by email. Returns True only on a confirmed send.

    On any failure (including no API key configured) this logs the link
    and returns False rather than raising — callers must not let a send
    failure change the response shown to the requester.
    """
    config = get_email_config()
    if config is None:
        # WARNING, not INFO: this app never configures logging, so the
        # default root logger drops INFO records. This line is the only
        # place the reset link surfaces when Resend isn't set up, and it
        # must actually show up in `uvicorn` console output / Railway logs.
        logger.warning("Resend not configured — password reset link for %s: %s", to_email, reset_url)
        return False

    payload = {
        "from": config.from_address,
        "to": [to_email],
        "subject": f"Reset your {business_name} admin password",
        "text": (
            f"Someone requested a password reset for the {business_name} admin panel.\n\n"
            f"Reset your password here (link expires in 30 minutes):\n{reset_url}\n\n"
            "If you didn't request this, you can ignore this email."
        ),
    }

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        logger.warning("Password reset link for %s: %s", to_email, reset_url)
        return False
