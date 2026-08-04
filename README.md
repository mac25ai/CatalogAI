# CatalogAI — by MAC25AI

A configurable, AI-powered product catalogue system for WhatsApp-first small businesses in India.

Small businesses manually send product photos to every customer on WhatsApp — no links, no catalogue, no scale. CatalogAI gives each client a beautiful, branded catalogue with an "Order on WhatsApp" button on every product. MAC25AI sets it up and manages it; clients touch nothing technical.

---

## Quick start

```bash
# 1. Create a virtual environment (first time only)
python -m venv venv

# 2. Activate it
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies (first time only)
pip install -r requirements.txt

# 4. Run the app
uvicorn main:app --reload --port 8000
```

That's it. No environment variables, no database, no external services.

## Test URLs

| URL | What it is |
|-----|------------|
| http://localhost:8000/ | CatalogAI landing page |
| http://localhost:8000/shop/zara-perfumes | Demo shop 1 (perfumes) |
| http://localhost:8000/shop/zara-perfumes/product/royal-oud-50ml | Product detail page |
| http://localhost:8000/shop/zara-perfumes/search?q=oud | Search results |
| http://localhost:8000/shop/zara-perfumes/about | About + FAQs |
| http://localhost:8000/shop/henna-house | Demo shop 2 (henna) |
| http://localhost:8000/admin/zara-perfumes/login | Admin panel (password: `admin123`) |
| http://localhost:8000/admin/henna-house/login | Admin panel (password: `admin456`) |
| http://localhost:8000/health | Health check |

Tip: open Chrome DevTools and switch to a 375px mobile viewport — every page is designed mobile-first.

## How it works

- **One config file per client** — `clients/[slug]/config.json` holds the business info, brand colors, categories, products, and FAQs. Zero code changes per client.
- **Adding a new client** — copy `clients/_template/` to `clients/[new-slug]/`, fill in the config, add a password to `admin_credentials.json`. The shop is live at `/shop/[new-slug]` immediately.
- **Admin panel** — each client gets `/admin/[slug]` to add/edit/delete products, toggle stock, and edit business settings. Changes write straight back to their config.json.
- **WhatsApp everywhere** — every order/share/contact action is a `wa.me` link. No WhatsApp API, no approval process.
- **Chatbot** — floating assistant on every shop page. Currently answers with mock keyword-matched responses from the client's config; the engineer swaps in the Claude API (see below).

## Project structure

```
main.py                  FastAPI entry point, landing page, 404, /health
routers/
  catalogue.py           Public shop pages (/shop/[slug]/...)
  admin.py               Admin panel (/admin/[slug]/...)
  chatbot.py             Chat API (/api/chat/[slug]) — mock responses
services/
  config_loader.py       Reads/validates/caches/writes client configs
  search.py              Keyword search across products
templates/               Jinja2 templates (base, shop, admin, components)
static/                  custom.css + gallery/variants/chatbot/search JS
clients/                 One folder per client with config.json
admin_credentials.json   slug → password for the admin panel
```

## Engineer handover — what to add next

1. **Real Claude API chatbot** — in `routers/chatbot.py`, replace `mock_response()` (marked with an `# ENGINEER:` comment). `pip install anthropic`, model `claude-sonnet-4-6`, pass the full product catalogue + FAQs as system context, API key from `ANTHROPIC_API_KEY`.
2. **Railway deployment** — add `railway.toml` with the uvicorn start command, connect the GitHub repo, set `ANTHROPIC_API_KEY` in the Railway dashboard.
3. **Database migration (optional)** — swap the JSON files in `clients/` for PostgreSQL (tables: clients, categories, products, faqs). Keep the `config_loader.py` interface the same; only the data source changes.
4. **Proper authentication** — replace plaintext passwords in `admin_credentials.json` with hashed passwords or OAuth, and move the session secret key in `main.py` to an environment variable.

## Business model

MAC25AI charges clients ₹8,000–25,000 setup + ₹1,500–3,500/month, fully managed. No payment gateway by design — all orders close on WhatsApp.

---

Built by MAC25AI · Calicut, Kerala · [mac25ai.com](https://mac25ai.com)
