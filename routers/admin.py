"""Admin panel routes: /admin/[slug]/...

Simple file-based admin. Reads and writes clients/[slug]/config.json directly.
Auth: username (from config) + password, kept in a session cookie.

Password sources, checked in priority order:
1. clients/[slug]/admin_override.json — written when a client changes their
   own password from the dashboard; overrides everything below.
2. ADMIN_PASS_[SLUG] env var (production/Railway).
3. admin_credentials.json — gitignored local-dev fallback.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from collections import Counter

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from routers.chatbot import unmatched_queries_path
from services.config_loader import load_config, save_config
from services.email_service import send_password_reset_email

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

CREDENTIALS_FILE = "admin_credentials.json"
PBKDF2_ITERATIONS = 200_000
RESET_TOKEN_TTL_SECONDS = 30 * 60
INTEREST_REPORT_WINDOW_DAYS = 7


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, digest = stored.partition("$")
    if not salt or not digest:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS).hex()
    return hmac.compare_digest(candidate, digest)


def override_path(slug: str) -> str:
    return f"clients/{slug}/admin_override.json"


def get_password_override(slug: str) -> str | None:
    path = override_path(slug)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("password_hash")


def set_password_override(slug: str, new_password: str):
    with open(override_path(slug), "w", encoding="utf-8") as f:
        json.dump({"password_hash": hash_password(new_password)}, f)


def reset_token_path(slug: str) -> str:
    return f"clients/{slug}/reset_token.json"


def create_reset_token(slug: str) -> str:
    """Generate a reset token, store only its hash + expiry, return the raw token."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with open(reset_token_path(slug), "w", encoding="utf-8") as f:
        json.dump({"token_hash": token_hash, "expires_at": time.time() + RESET_TOKEN_TTL_SECONDS}, f)
    return token


def verify_reset_token(slug: str, token: str) -> bool:
    if not token:
        return False
    path = reset_token_path(slug)
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if time.time() > data.get("expires_at", 0):
        return False
    candidate = hashlib.sha256(token.encode()).hexdigest()
    return hmac.compare_digest(candidate, data.get("token_hash", ""))


def clear_reset_token(slug: str):
    path = reset_token_path(slug)
    if os.path.exists(path):
        os.remove(path)


def check_password(slug: str, password: str) -> bool:
    override = get_password_override(slug)
    if override is not None:
        return verify_password(password, override)

    env_key = f"ADMIN_PASS_{slug.upper().replace('-', '_')}"
    env_password = os.environ.get(env_key)
    if env_password is not None:
        return env_password == password

    if not os.path.exists(CREDENTIALS_FILE):
        return False
    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        credentials = json.load(f)
    return credentials.get(slug) == password


def expected_username(config: dict, slug: str) -> str:
    return config["business"].get("admin_username") or slug.replace("-", "")


def check_username(config: dict, slug: str, username: str) -> bool:
    return username.strip().lower() == expected_username(config, slug).lower()


def is_logged_in(request: Request, slug: str) -> bool:
    return request.session.get("admin_slug") == slug


def require_login(request: Request, slug: str):
    """Return a redirect to the login page if not authenticated, else None."""
    if not is_logged_in(request, slug):
        return RedirectResponse(url=f"/admin/{slug}/login", status_code=303)
    return None


def get_config_or_404(slug: str) -> dict:
    config = load_config(slug)
    if config is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return config


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "product"


def unique_product_id(config: dict, base: str) -> str:
    existing = {p["id"] for p in config["products"]}
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


ORDER_STATUSES = ("Received", "Packed", "Shipped", "Delivered")


def unique_order_id(config: dict, base: str) -> str:
    existing = {o["id"] for o in config.get("orders", [])}
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


async def parse_product_form(request: Request, config: dict) -> dict:
    """Build a product dict from the submitted add/edit form."""
    form = await request.form()

    images = [
        line.strip()
        for line in (form.get("images") or "").splitlines()
        if line.strip()
    ]
    tags = [t.strip() for t in (form.get("tags") or "").split(",") if t.strip()]

    # Variant groups come as parallel lists: variant_name[] + variant_options[]
    variant_names = form.getlist("variant_name")
    variant_options = form.getlist("variant_options")
    variants = []
    for name, options in zip(variant_names, variant_options):
        name = name.strip()
        opts = [o.strip() for o in options.split(",") if o.strip()]
        if name and opts:
            variants.append({"name": name, "options": opts})

    try:
        price = int(float(form.get("price") or 0))
    except ValueError:
        price = 0

    try:
        min_order_qty = max(1, int(form.get("min_order_qty") or 1))
    except ValueError:
        min_order_qty = 1

    return {
        "name": (form.get("name") or "").strip(),
        "category_id": form.get("category_id") or "",
        "short_description": (form.get("short_description") or "").strip(),
        "long_description": (form.get("long_description") or "").strip(),
        "price": price,
        "price_hidden": form.get("price_hidden") == "on",
        "images": images,
        "variants": variants,
        "in_stock": form.get("in_stock") == "on",
        "featured": form.get("featured") == "on",
        "bestseller": form.get("bestseller") == "on",
        "min_order_qty": min_order_qty,
        "tags": tags,
    }


# ---------------------------------------------------------------- auth


@router.get("/{slug}/login", response_class=HTMLResponse)
async def login_page(request: Request, slug: str):
    config = get_config_or_404(slug)
    if is_logged_in(request, slug):
        return RedirectResponse(url=f"/admin/{slug}/dashboard", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "username": expected_username(config, slug),
            "error": None,
            "reset": request.query_params.get("reset") == "1",
        },
    )


@router.post("/{slug}/login", response_class=HTMLResponse)
async def login_submit(request: Request, slug: str):
    config = get_config_or_404(slug)
    form = await request.form()
    username = form.get("username") or ""
    password = form.get("password") or ""
    if check_username(config, slug, username) and check_password(slug, password):
        request.session["admin_slug"] = slug
        return RedirectResponse(url=f"/admin/{slug}/dashboard", status_code=303)
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "username": username,
            "error": "Incorrect username or password. Please try again.",
            "reset": False,
        },
        status_code=401,
    )


@router.get("/{slug}/logout")
async def logout(request: Request, slug: str):
    request.session.pop("admin_slug", None)
    return RedirectResponse(url=f"/admin/{slug}/login", status_code=303)


# ---------------------------------------------------------------- dashboard


@router.get("/{slug}/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    products = config["products"]
    stats = {
        "total": len(products),
        "in_stock": sum(1 for p in products if p.get("in_stock")),
        "out_of_stock": sum(1 for p in products if not p.get("in_stock")),
        "categories": len(config["categories"]),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "products": products,
            "category_map": config["_category_map"],
            "stats": stats,
        },
    )


# ---------------------------------------------------------------- reports


def load_recent_unmatched_queries(slug: str, days: int = INTEREST_REPORT_WINDOW_DAYS) -> list[dict]:
    path = unmatched_queries_path(slug)
    if not os.path.exists(path):
        return []
    cutoff = time.time() - days * 86400
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("timestamp", 0) >= cutoff and entry.get("query"):
                entries.append(entry)
    return entries


@router.get("/{slug}/reports/interest", response_class=HTMLResponse)
async def interest_report(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    entries = load_recent_unmatched_queries(slug)
    counts = Counter(entry["query"].strip().lower() for entry in entries)
    return templates.TemplateResponse(
        "admin/interest_report.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "top_queries": counts.most_common(50),
            "total_queries": len(entries),
            "window_days": INTEREST_REPORT_WINDOW_DAYS,
        },
    )


# ---------------------------------------------------------------- products


@router.get("/{slug}/product/new", response_class=HTMLResponse)
async def product_new_page(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "categories": config["categories"],
            "product": None,
            "form_title": "Add New Product",
            "form_action": f"/admin/{slug}/product/new",
        },
    )


@router.post("/{slug}/product/new")
async def product_new_submit(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    product = await parse_product_form(request, config)
    product["id"] = unique_product_id(config, slugify(product["name"]))
    # Insert id first so the saved JSON reads naturally
    product = {"id": product["id"], **{k: v for k, v in product.items() if k != "id"}}
    config["products"].append(product)
    save_config(slug, config)
    return RedirectResponse(url=f"/admin/{slug}/dashboard", status_code=303)


@router.get("/{slug}/product/{product_id}/edit", response_class=HTMLResponse)
async def product_edit_page(request: Request, slug: str, product_id: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    product = config["_product_map"].get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "categories": config["categories"],
            "product": product,
            "form_title": f"Edit: {product['name']}",
            "form_action": f"/admin/{slug}/product/{product_id}/edit",
        },
    )


@router.post("/{slug}/product/{product_id}/edit")
async def product_edit_submit(request: Request, slug: str, product_id: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    updated = await parse_product_form(request, config)
    for i, p in enumerate(config["products"]):
        if p["id"] == product_id:
            config["products"][i] = {"id": product_id, **updated}
            break
    else:
        raise HTTPException(status_code=404, detail="Product not found")
    save_config(slug, config)
    return RedirectResponse(url=f"/admin/{slug}/dashboard", status_code=303)


@router.post("/{slug}/product/{product_id}/delete")
async def product_delete(request: Request, slug: str, product_id: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    config["products"] = [p for p in config["products"] if p["id"] != product_id]
    save_config(slug, config)
    return RedirectResponse(url=f"/admin/{slug}/dashboard", status_code=303)


@router.post("/{slug}/product/{product_id}/toggle-stock")
async def product_toggle_stock(request: Request, slug: str, product_id: str):
    """AJAX endpoint: flip in_stock and return the new state (no page reload)."""
    if not is_logged_in(request, slug):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    config = get_config_or_404(slug)
    for p in config["products"]:
        if p["id"] == product_id:
            p["in_stock"] = not p.get("in_stock", True)
            save_config(slug, config)
            return JSONResponse({"id": product_id, "in_stock": p["in_stock"]})
    return JSONResponse({"error": "Product not found"}, status_code=404)


# ---------------------------------------------------------------- orders


@router.get("/{slug}/orders", response_class=HTMLResponse)
async def orders_list(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    orders = sorted(config.get("orders", []), key=lambda o: o.get("created_at", 0), reverse=True)
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "orders": orders,
            "statuses": ORDER_STATUSES,
        },
    )


@router.get("/{slug}/order/new", response_class=HTMLResponse)
async def order_new_page(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "admin/order_form.html",
        {"request": request, "slug": slug, "business": config["business"]},
    )


@router.post("/{slug}/order/new")
async def order_new_submit(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    form = await request.form()
    customer_name = (form.get("customer_name") or "").strip()
    customer_phone = (form.get("customer_phone") or "").strip()
    items = (form.get("items") or "").strip()

    order = {
        "id": unique_order_id(config, slugify(customer_name or "order")),
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "items": items,
        "status": ORDER_STATUSES[0],
        "created_at": time.time(),
    }
    config.setdefault("orders", []).append(order)
    save_config(slug, config)
    return RedirectResponse(url=f"/admin/{slug}/orders", status_code=303)


@router.post("/{slug}/order/{order_id}/status")
async def order_update_status(request: Request, slug: str, order_id: str):
    """AJAX endpoint: set an order's status and return the new state (no page reload)."""
    if not is_logged_in(request, slug):
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    form = await request.form()
    new_status = form.get("status") or ""
    if new_status not in ORDER_STATUSES:
        return JSONResponse({"error": "Invalid status"}, status_code=400)
    config = get_config_or_404(slug)
    for order in config.get("orders", []):
        if order["id"] == order_id:
            order["status"] = new_status
            save_config(slug, config)
            return JSONResponse({"id": order_id, "status": new_status})
    return JSONResponse({"error": "Order not found"}, status_code=404)


# ---------------------------------------------------------------- settings


@router.get("/{slug}/settings", response_class=HTMLResponse)
async def settings_page(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "saved": request.query_params.get("saved") == "1",
        },
    )


@router.post("/{slug}/settings")
async def settings_submit(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    form = await request.form()
    business = config["business"]
    # Slug is the folder name / URL — never editable from the form
    editable = [
        "name", "tagline", "about", "logo_url", "primary_color",
        "secondary_color", "whatsapp_number", "whatsapp_greeting", "location",
        "hours", "instagram_url", "facebook_url", "google_maps_url",
        "language", "chatbot_name", "chatbot_greeting", "admin_email",
    ]
    for field in editable:
        if field in form:
            business[field] = (form.get(field) or "").strip()
    save_config(slug, config)
    return RedirectResponse(url=f"/admin/{slug}/settings?saved=1", status_code=303)


# ---------------------------------------------------------------- password


@router.get("/{slug}/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "admin/change_password.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "error": None,
            "saved": request.query_params.get("saved") == "1",
        },
    )


@router.post("/{slug}/change-password", response_class=HTMLResponse)
async def change_password_submit(request: Request, slug: str):
    redirect = require_login(request, slug)
    if redirect:
        return redirect
    config = get_config_or_404(slug)
    form = await request.form()
    current_password = form.get("current_password") or ""
    new_password = form.get("new_password") or ""
    confirm_password = form.get("confirm_password") or ""

    error = None
    if not check_password(slug, current_password):
        error = "Current password is incorrect."
    elif len(new_password) < 8:
        error = "New password must be at least 8 characters."
    elif new_password != confirm_password:
        error = "New password and confirmation don't match."

    if error:
        return templates.TemplateResponse(
            "admin/change_password.html",
            {
                "request": request,
                "slug": slug,
                "business": config["business"],
                "error": error,
                "saved": False,
            },
            status_code=400,
        )

    set_password_override(slug, new_password)
    return RedirectResponse(url=f"/admin/{slug}/change-password?saved=1", status_code=303)


# ---------------------------------------------------------------- forgot / reset password


@router.get("/{slug}/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request, slug: str):
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "admin/forgot_password.html",
        {"request": request, "slug": slug, "business": config["business"], "sent": False},
    )


@router.post("/{slug}/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(request: Request, slug: str):
    config = get_config_or_404(slug)
    form = await request.form()
    submitted_email = (form.get("email") or "").strip().lower()

    on_file_email = (config["business"].get("admin_email") or "").strip().lower()
    if on_file_email and submitted_email == on_file_email:
        token = create_reset_token(slug)
        reset_url = str(request.base_url).rstrip("/") + f"/admin/{slug}/reset-password?token={token}"
        send_password_reset_email(config["business"]["name"], on_file_email, reset_url)

    # Always the same response, whether or not the email matched, so this
    # never reveals whether a recovery email is configured for this account.
    return templates.TemplateResponse(
        "admin/forgot_password.html",
        {"request": request, "slug": slug, "business": config["business"], "sent": True},
    )


@router.get("/{slug}/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, slug: str):
    config = get_config_or_404(slug)
    token = request.query_params.get("token") or ""
    valid = verify_reset_token(slug, token)
    return templates.TemplateResponse(
        "admin/reset_password.html",
        {
            "request": request,
            "slug": slug,
            "business": config["business"],
            "valid": valid,
            "token": token,
            "error": None,
        },
        status_code=200 if valid else 400,
    )


@router.post("/{slug}/reset-password", response_class=HTMLResponse)
async def reset_password_submit(request: Request, slug: str):
    config = get_config_or_404(slug)
    form = await request.form()
    token = form.get("token") or ""
    new_password = form.get("new_password") or ""
    confirm_password = form.get("confirm_password") or ""

    if not verify_reset_token(slug, token):
        return templates.TemplateResponse(
            "admin/reset_password.html",
            {"request": request, "slug": slug, "business": config["business"], "valid": False, "token": token, "error": None},
            status_code=400,
        )

    error = None
    if len(new_password) < 8:
        error = "New password must be at least 8 characters."
    elif new_password != confirm_password:
        error = "New password and confirmation don't match."

    if error:
        return templates.TemplateResponse(
            "admin/reset_password.html",
            {"request": request, "slug": slug, "business": config["business"], "valid": True, "token": token, "error": error},
            status_code=400,
        )

    set_password_override(slug, new_password)
    clear_reset_token(slug)
    return RedirectResponse(url=f"/admin/{slug}/login?reset=1", status_code=303)
