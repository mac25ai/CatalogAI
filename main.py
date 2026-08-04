"""CatalogAI — WhatsApp-first product catalogue system by MAC25AI.

Entry point: mounts static files, session middleware, and all routers.

Run with:
    uvicorn main:app --reload --port 8000
"""

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from routers import catalogue, admin, chatbot
from services.config_loader import list_clients, load_config

app = FastAPI(title="CatalogAI", docs_url=None, redoc_url=None)

# Session cookie signing key. Falls back to a local-dev default so
# `uvicorn main:app` still needs zero env vars locally; set SESSION_SECRET
# in Railway before deploying.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "catalogai-local-dev-secret"),
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(catalogue.router)
app.include_router(admin.router)
app.include_router(chatbot.router)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """CatalogAI landing page (MAC25AI brand) with links to demo shops."""
    clients = []
    for slug in list_clients():
        config = load_config(slug)
        if config:
            clients.append(config["business"])
    return templates.TemplateResponse(
        "landing.html", {"request": request, "clients": clients}
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse(
        "404.html", {"request": request}, status_code=404
    )
