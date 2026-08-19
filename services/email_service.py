"""Password-reset email sending.

Real sending happens over SMTP (stdlib only, no new dependency) if
SMTP_HOST/SMTP_USER/SMTP_PASSWORD are set. Without them, the reset link is
logged instead so local dev needs zero env vars and MAC25AI can still relay
a link manually (e.g. over WhatsApp) from the Railway log viewer until a
client's SMTP is configured.
"""

import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    user: str
    password: str
    from_address: str


def get_smtp_config() -> SmtpConfig | None:
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not host or not user or not password:
        return None
    return SmtpConfig(
        host=host,
        port=int(os.environ.get("SMTP_PORT", "587")),
        user=user,
        password=password,
        from_address=os.environ.get("SMTP_FROM", user),
    )


def send_password_reset_email(business_name: str, to_email: str, reset_url: str) -> bool:
    """Send the reset link by email. Returns True only on a confirmed send.

    On any failure (including no SMTP configured) this logs the link and
    returns False rather than raising — callers must not let a send failure
    change the response shown to the requester.
    """
    config = get_smtp_config()
    if config is None:
        # WARNING, not INFO: this app never configures logging, so the
        # default root logger drops INFO records. This line is the only
        # place the reset link surfaces when SMTP isn't set up, and it must
        # actually show up in `uvicorn` console output / Railway logs.
        logger.warning("SMTP not configured — password reset link for %s: %s", to_email, reset_url)
        return False

    message = EmailMessage()
    message["Subject"] = f"Reset your {business_name} admin password"
    message["From"] = config.from_address
    message["To"] = to_email
    message.set_content(
        f"Someone requested a password reset for the {business_name} admin panel.\n\n"
        f"Reset your password here (link expires in 30 minutes):\n{reset_url}\n\n"
        "If you didn't request this, you can ignore this email."
    )

    try:
        with smtplib.SMTP(config.host, config.port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(config.user, config.password)
            smtp.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        logger.warning("Password reset link for %s: %s", to_email, reset_url)
        return False
