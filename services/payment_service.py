"""Payment link generation for chat-confirmed orders.

Two ways to get a customer a payable link, tried in order by callers:

1. Razorpay Payment Links API (https://api.razorpay.com/v1/payment_links)
   via httpx -- no Razorpay SDK dependency, same approach services/
   email_service.py already uses for Resend. Requires a Razorpay account
   and RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET.
2. A plain UPI deep link (upi://pay?...) built from the client's own UPI
   ID (business.upi_id in their config, set from their existing GPay/
   PhonePe/Paytm business account -- the same ID behind whatever QR code
   they already have printed at their counter). No account signup, no API
   key, no per-transaction fee, works the moment the client sets one
   field in their Settings page. Opens the customer's own UPI app with
   the amount already filled in; they just confirm.

If neither is configured, callers fall back to a plain "we'll follow up on
WhatsApp" reply instead of a link.
"""

import logging
import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

RAZORPAY_API_URL = "https://api.razorpay.com/v1/payment_links"


@dataclass(frozen=True)
class RazorpayConfig:
    key_id: str
    key_secret: str


def get_razorpay_config() -> RazorpayConfig | None:
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        return None
    return RazorpayConfig(key_id=key_id, key_secret=key_secret)


def create_payment_link(amount_rupees: int, description: str, customer_name: str, customer_phone: str) -> str | None:
    """Create a Razorpay payment link and return its short_url.

    Returns None on any failure, including missing config -- callers must
    handle a None result gracefully rather than assuming a link exists.
    """
    config = get_razorpay_config()
    if config is None:
        logger.warning("Razorpay not configured — no payment link generated for %s (%s)", customer_name, description)
        return None

    payload = {
        "amount": amount_rupees * 100,  # Razorpay wants paise, not rupees
        "currency": "INR",
        "description": description,
        "customer": {"name": customer_name, "contact": customer_phone},
        "notify": {"sms": True},
        "reminder_enable": True,
    }

    try:
        response = httpx.post(
            RAZORPAY_API_URL,
            auth=(config.key_id, config.key_secret),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("short_url")
    except Exception:
        logger.exception("Failed to create Razorpay payment link for %s", customer_name)
        return None


def build_upi_payment_link(upi_id: str, payee_name: str, amount_rupees: int, note: str) -> str:
    """Build a upi://pay deep link that opens the customer's UPI app with
    the amount pre-filled. Pure string building, no network call, no
    account or API key needed -- upi_id is the client's own UPI ID."""
    params = {
        "pa": upi_id,
        "pn": payee_name,
        "am": str(amount_rupees),
        "cu": "INR",
        "tn": note,
    }
    query = "&".join(f"{key}={quote(value)}" for key, value in params.items())
    return f"upi://pay?{query}"
