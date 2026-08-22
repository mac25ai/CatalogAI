"""Payment link generation for chat-confirmed orders.

Uses Razorpay's Payment Links API (https://api.razorpay.com/v1/payment_links)
via httpx -- no Razorpay SDK dependency, same approach services/email_service.py
already uses for Resend. Without RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET configured,
link creation is skipped and logged instead, so local dev and any client that
hasn't set up Razorpay yet keep working with zero env vars, and the chat flow
falls back to a plain "we'll follow up on WhatsApp" reply instead of a link.
"""

import logging
import os
from dataclasses import dataclass

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
