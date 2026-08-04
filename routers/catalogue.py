"""Public catalogue routes: /shop/[slug]/..."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.config_loader import load_config
from services.search import search_products

router = APIRouter(prefix="/shop", tags=["catalogue"])
templates = Jinja2Templates(directory="templates")


def get_config_or_404(slug: str) -> dict:
    config = load_config(slug)
    if config is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return config


def shop_context(request: Request, config: dict, **extra) -> dict:
    """Base template context shared by every shop page."""
    ctx = {
        "request": request,
        "config": config,
        "business": config["business"],
        "slug": config["business"]["slug"],
    }
    ctx.update(extra)
    return ctx


@router.get("/{slug}", response_class=HTMLResponse)
async def shop_home(request: Request, slug: str):
    config = get_config_or_404(slug)
    products = config["products"]
    featured = [p for p in products if p.get("featured")]
    categories = sorted(config["categories"], key=lambda c: c.get("display_order", 99))
    # Product count per category for the grid
    category_counts = {
        c["id"]: sum(1 for p in products if p.get("category_id") == c["id"])
        for c in categories
    }
    return templates.TemplateResponse(
        "shop/home.html",
        shop_context(
            request,
            config,
            featured=featured,
            categories=categories,
            category_counts=category_counts,
            products=products,
        ),
    )


@router.get("/{slug}/category/{category_id}", response_class=HTMLResponse)
async def shop_category(request: Request, slug: str, category_id: str):
    config = get_config_or_404(slug)
    category = config["_category_map"].get(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    products = [p for p in config["products"] if p.get("category_id") == category_id]
    return templates.TemplateResponse(
        "shop/category.html",
        shop_context(request, config, category=category, products=products),
    )


@router.get("/{slug}/product/{product_id}", response_class=HTMLResponse)
async def shop_product(request: Request, slug: str, product_id: str):
    config = get_config_or_404(slug)
    product = config["_product_map"].get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    category = config["_category_map"].get(product.get("category_id"))
    product_url = str(request.url)
    return templates.TemplateResponse(
        "shop/product.html",
        shop_context(
            request,
            config,
            product=product,
            category=category,
            product_url=product_url,
        ),
    )


@router.get("/{slug}/search", response_class=HTMLResponse)
async def shop_search(request: Request, slug: str, q: str = ""):
    config = get_config_or_404(slug)
    results = search_products(config, q)
    return templates.TemplateResponse(
        "shop/search.html",
        shop_context(request, config, query=q, results=results),
    )


@router.get("/{slug}/about", response_class=HTMLResponse)
async def shop_about(request: Request, slug: str):
    config = get_config_or_404(slug)
    return templates.TemplateResponse(
        "shop/about.html",
        shop_context(request, config, faqs=config.get("faqs", [])),
    )
