"""Config loader service.

Reads, validates, and caches client config.json files.
Each client lives in clients/[slug]/config.json — this is the ONLY
thing that changes per client. Zero code changes ever.
"""

import json
import os
from typing import Optional

# In-memory cache: slug -> parsed config dict
config_cache = {}

CLIENTS_DIR = "clients"


def load_config(slug: str) -> Optional[dict]:
    """Load and cache a client's config. Returns None if the client doesn't exist."""
    if slug in config_cache:
        return config_cache[slug]

    path = os.path.join(CLIENTS_DIR, slug, "config.json")
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validation
    assert config["business"]["slug"] == slug, f"Slug mismatch in config for {slug}"
    assert len(config.get("categories", [])) > 0, f"No categories in config for {slug}"
    assert len(config.get("products", [])) > 0, f"No products in config for {slug}"

    # Build lookup maps for fast access
    config["_category_map"] = {c["id"]: c for c in config["categories"]}
    config["_product_map"] = {p["id"]: p for p in config["products"]}

    config_cache[slug] = config
    return config


def save_config(slug: str, config: dict):
    """Write a client's config back to disk and clear its cache entry."""
    path = os.path.join(CLIENTS_DIR, slug, "config.json")
    # Remove internal lookup maps before saving
    config_to_save = {k: v for k, v in config.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config_to_save, f, indent=2, ensure_ascii=False)
    # Clear cache for this slug so next request reloads
    config_cache.pop(slug, None)


def list_clients() -> list:
    """List all client slugs (folders in clients/ that contain a config.json)."""
    clients = []
    if not os.path.exists(CLIENTS_DIR):
        return clients
    for folder in os.listdir(CLIENTS_DIR):
        if folder.startswith("_"):
            continue
        config_path = os.path.join(CLIENTS_DIR, folder, "config.json")
        if os.path.exists(config_path):
            clients.append(folder)
    return clients
