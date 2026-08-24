"""Shared order-record helpers.

Used by both the admin CRUD routes (routers/admin.py) and the chat
order-confirmation flow (routers/chatbot.py). Kept in its own module
rather than one router importing from the other, since admin.py already
imports from chatbot.py (unmatched_queries_path) -- routers importing
each other directly would create a circular import.
"""

import time

# "Awaiting Payment" / "Paid" are set by the chat payment-link flow;
# "Received" is the default for orders entered manually via the admin
# panel. All six are valid targets in the admin orders dropdown.
ORDER_STATUSES = ("Received", "Awaiting Payment", "Paid", "Packed", "Shipped", "Delivered")


def unique_order_id(config: dict, base: str) -> str:
    existing = {o["id"] for o in config.get("orders", [])}
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def add_order(
    config: dict,
    *,
    id_base: str,
    customer_name: str,
    customer_phone: str,
    items: str,
    status: str = ORDER_STATUSES[0],
) -> dict:
    """Append a new order to config["orders"] and return it. Does not save
    to disk -- the caller is responsible for calling save_config."""
    order = {
        "id": unique_order_id(config, id_base),
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items,
        "status": status,
        "created_at": time.time(),
    }
    config.setdefault("orders", []).append(order)
    return order
