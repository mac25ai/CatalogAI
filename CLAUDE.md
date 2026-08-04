# CLAUDE.md — CatalogAI by MAC25AI

## READ THIS FIRST

This file is your complete specification. Read every section before writing a single line of code.
You are building a production-quality WhatsApp-first product catalogue system for small businesses in India.
The founder is non-technical. Explain every terminal command before running it.

---

## WHO YOU ARE WORKING WITH

- **Founder:** Abinas V, MAC25AI (mac25ai.com), Calicut, Kerala, India
- **Your role:** Primary builder. Build everything described here in one session.
- **Abinas's background:** Non-developer. Uses Claude Code for all technical work.
- **Engineer handover:** An AIML engineer will take this codebase and add: real Claude API chatbot, Railway deployment, and production database. Your job is to build everything else so they have 80% done.

---

## WHAT YOU ARE BUILDING

**CatalogAI** — A configurable, AI-powered product catalogue system for WhatsApp-first small businesses.

**The pain:** Small businesses in Kerala manually send product photos to every customer on WhatsApp. No product links, no catalogue, no scale. CatalogAI gives them a beautiful catalogue with a WhatsApp order button — set up by MAC25AI, not by the client.

**Business model:** MAC25AI charges clients ₹8,000–25,000 setup + ₹1,500–3,500/month. MAC25AI manages everything. Clients touch nothing technical.

---

## BUILD GOAL FOR THIS SESSION

Build the **complete CatalogAI application** — all pages, all features, all templates — running 100% locally.

### What to build in this session (in this order):

1. Full project file structure
2. FastAPI backend with all routes
3. Config loader (reads JSON, validates, caches)
4. All Jinja2 templates (mobile-first, beautiful)
5. Product catalogue — homepage, category page, product detail page
6. WhatsApp integration on every page
7. Chatbot UI — floating button, chat window, mock responses
8. Admin panel — view, add, edit, delete products, toggle stock
9. Search page (keyword search across products)
10. About/contact page per client
11. 404 page
12. Demo client configs — zara-perfumes (perfume business, 6 products) and henna-house (henna business, 5 products)
13. All static JS files (image gallery, variant selector, chatbot widget, search)

### What NOT to build in this session:

- ❌ Railway deployment config (engineer adds this)
- ❌ Real Claude API chatbot (engineer adds this — use mock responses)
- ❌ PostgreSQL or any database (JSON files only)
- ❌ Environment variables or .env file (nothing should require one)
- ❌ GitHub setup (engineer handles this)
- ❌ Custom domains (Phase 2)
- ❌ Payment gateway (never — by design)

### Single command to run the whole thing:
```bash
uvicorn main:app --reload --port 8000
```
Nothing else should be needed. No env vars. No external services.

---

## TECH STACK (LOCAL ONLY)

| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | FastAPI (Python) | Simple, fast, Claude Code knows it well |
| Templating | Jinja2 | Server-side HTML, no build step |
| Styling | Tailwind CSS via CDN | No build tools, great mobile defaults |
| Icons | Heroicons via CDN (unpkg) | Clean, consistent icons |
| Database | None — JSON files | No setup needed, engineer migrates to DB later |
| Images | External URLs in config | Clients use imgbb.com (free), paste URL |
| AI Chatbot | Mock responses (see spec) | Engineer replaces with Claude API later |
| Server | uvicorn | Standard FastAPI server |

---

## FILE STRUCTURE (CREATE EXACTLY THIS)

```
catalogai/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── main.py                          ← FastAPI app entry, all route mounting
├── routers/
│   ├── catalogue.py                 ← /shop/[slug] routes
│   ├── admin.py                     ← /admin/[slug] routes
│   └── chatbot.py                   ← /api/chat route (mock)
├── services/
│   ├── config_loader.py             ← reads/validates/caches client JSON
│   └── search.py                    ← product search logic
├── templates/
│   ├── base.html                    ← base layout: nav, WhatsApp button, footer, CSS vars
│   ├── landing.html                 ← CatalogAI landing page (MAC25AI brand)
│   ├── shop/
│   │   ├── home.html                ← client catalogue homepage
│   │   ├── category.html            ← products in a category
│   │   ├── product.html             ← single product detail page
│   │   ├── search.html              ← search results page
│   │   └── about.html               ← about/contact page for client
│   ├── admin/
│   │   ├── login.html               ← simple admin login (hardcoded for now)
│   │   ├── dashboard.html           ← product list with actions
│   │   ├── product_form.html        ← add/edit product form
│   │   └── settings.html            ← business info edit form
│   ├── components/
│   │   ├── product_card.html        ← reusable product card macro
│   │   ├── chatbot_widget.html      ← floating chatbot button + window
│   │   └── whatsapp_button.html     ← floating WhatsApp button
│   └── 404.html
├── static/
│   ├── css/
│   │   └── custom.css               ← minor overrides on Tailwind
│   └── js/
│       ├── gallery.js               ← image gallery switcher on product page
│       ├── variants.js              ← variant selector + dynamic WhatsApp message
│       ├── chatbot.js               ← chatbot open/close/send/receive logic
│       └── search.js                ← live search filtering
├── clients/
│   ├── _template/
│   │   └── config.json              ← master template for new clients
│   ├── zara-perfumes/
│   │   └── config.json              ← demo: perfume business (6 products)
│   └── henna-house/
│       └── config.json              ← demo: henna products business (5 products)
└── admin_credentials.json           ← simple admin credentials per client (no auth lib needed)
```

---

## CLIENT CONFIG SCHEMA

Every client has one file: `clients/[slug]/config.json`
This is the ONLY thing that changes per client. Zero code changes ever.

```json
{
  "business": {
    "name": "Business Name",
    "slug": "url-safe-slug",
    "tagline": "Short punchy tagline",
    "about": "2-3 sentences about the business.",
    "logo_url": "https://i.ibb.co/example/logo.png",
    "primary_color": "#1a1a2e",
    "secondary_color": "#e94560",
    "whatsapp_number": "919876543210",
    "whatsapp_greeting": "Hi! I just browsed your catalogue. Can you help me?",
    "location": "Calicut, Kerala",
    "hours": "Mon–Sat, 10AM–8PM",
    "instagram_url": "https://instagram.com/example",
    "facebook_url": "",
    "google_maps_url": "https://maps.google.com/?q=Calicut+Kerala",
    "language": "en",
    "chatbot_name": "Zara Assistant",
    "chatbot_greeting": "Hi! Welcome to Zara Perfumes 🌸 How can I help you today?"
  },
  "categories": [
    {
      "id": "oud-collection",
      "name": "Oud Collection",
      "image_url": "https://i.ibb.co/example/oud.jpg",
      "display_order": 1
    }
  ],
  "products": [
    {
      "id": "royal-oud-50ml",
      "name": "Royal Oud",
      "category_id": "oud-collection",
      "short_description": "A rich, woody fragrance with hints of rose.",
      "long_description": "Royal Oud is our signature fragrance — a deep, luxurious blend of aged oud wood, Bulgarian rose, and warm amber. Perfect for evening wear and special occasions. Lasts 8–10 hours on skin.",
      "price": 1500,
      "price_hidden": false,
      "images": [
        "https://i.ibb.co/example/royal-oud-1.jpg",
        "https://i.ibb.co/example/royal-oud-2.jpg",
        "https://i.ibb.co/example/royal-oud-3.jpg"
      ],
      "variants": [
        {
          "name": "Size",
          "options": ["30ml", "50ml", "100ml"]
        }
      ],
      "in_stock": true,
      "featured": true,
      "bestseller": false,
      "min_order_qty": 1,
      "tags": ["oud", "woody", "luxury", "evening"]
    }
  ],
  "faqs": [
    {
      "question": "Do you deliver outside Kerala?",
      "answer": "Yes! We ship all over India. Delivery takes 3–5 business days."
    },
    {
      "question": "What is your return policy?",
      "answer": "We accept returns within 7 days if the product is unopened."
    }
  ]
}
```

---

## URL STRUCTURE

```
/                                     → CatalogAI landing page
/shop/[slug]                          → Client catalogue homepage
/shop/[slug]/category/[category-id]   → Category product listing
/shop/[slug]/product/[product-id]     → Product detail page
/shop/[slug]/search?q=[query]         → Search results
/shop/[slug]/about                    → About/contact page
/api/chat/[slug]                      → Chatbot API endpoint (POST, returns mock)
/admin/[slug]/login                   → Admin login
/admin/[slug]/dashboard               → Product list
/admin/[slug]/product/new             → Add product
/admin/[slug]/product/[id]/edit       → Edit product
/admin/[slug]/settings                → Edit business info
/health                               → {"status": "ok"}
```

---

## TEMPLATE SPECIFICATIONS

### base.html
- Imports: Tailwind CSS CDN, Heroicons CDN
- Injects client brand colors as CSS variables:
  ```html
  <style>
    :root {
      --primary: {{ business.primary_color }};
      --secondary: {{ business.secondary_color }};
    }
  </style>
  ```
- Sticky top nav: logo left, business name, search icon, WhatsApp icon
- Floating WhatsApp button: fixed bottom-right, green (#25D366), always visible
- Floating chatbot button: fixed bottom-right above WhatsApp button, primary color
- Footer: business name, hours, location, social links
- Includes chatbot_widget.html component

### shop/home.html
- Hero section: logo, business name, tagline, about text, primary color background
- Featured products row (horizontal scroll on mobile): cards with image, name, price, WhatsApp share
- Categories grid: 2 columns on mobile, image + name, tappable
- All products section: 2-column grid on mobile
- "Powered by CatalogAI" small text at very bottom (MAC25AI branding)

### shop/category.html
- Category header: category image, category name, product count
- Product grid: 2 columns mobile, 3 columns desktop
- Each product card: image, name, short description, price, in-stock badge, "Order on WhatsApp" button

### shop/product.html
- Image gallery: main image large, thumbnails below (tap to switch — gallery.js)
- Product name (large), price, in-stock/out-of-stock badge
- Variant selectors: pill buttons for each variant group (variants.js updates WhatsApp message)
- Long description
- "Order on WhatsApp" button: large, green, full width on mobile
  - Message: "Hi, I'm interested in ordering [Product Name] – [Selected Variants]. Can you help?"
- "Share this product" button: sends product URL via WhatsApp
- Back to category link

### shop/search.html
- Search bar at top (pre-filled with query)
- Result count: "X products found for '[query]'"
- Product grid: same card as category page
- Empty state: "No products found. Try a different search." + WhatsApp button to ask directly

### shop/about.html
- Business name, logo, about text
- Business hours
- Location with Google Maps link button
- Contact: WhatsApp button, Instagram link, Facebook link
- FAQ accordion: each question/answer from config

### components/product_card.html (Jinja2 macro)
- Product image (aspect ratio 1:1, object-cover)
- Bestseller / Featured badge (top-left overlay)
- Out of Stock overlay (greyed, not hidden)
- Product name
- Short description (1 line, truncated)
- Price (or "Contact for price" if price_hidden)
- Two buttons: "View Details" and WhatsApp share icon

### components/chatbot_widget.html
- Floating button: bottom-right, above WhatsApp button, uses primary_color
- Shows chatbot_name from config
- Click opens chat window (slide up animation)
- Chat window: header with chatbot_name + close button, message thread, input + send button
- On open: shows chatbot_greeting message automatically
- Includes chatbot.js

### admin/login.html
- Simple centered form: slug (pre-filled, hidden), password field, login button
- Clean minimal design
- Note: credentials stored in admin_credentials.json

### admin/dashboard.html
- Header: "Admin — [Business Name]" + logout link
- Stats row: total products, in-stock count, out-of-stock count, category count
- Table: product name | category | price | stock status (toggle button) | edit button | delete button
- "Add New Product" button
- Link to view live catalogue

### admin/product_form.html
- Form fields: name, category (dropdown), short description, long description,
  price (number), price_hidden (checkbox), images (textarea, one URL per line),
  variant groups (dynamic add/remove), in_stock (toggle), featured (checkbox), bestseller (checkbox),
  tags (comma-separated)
- Save button

### admin/settings.html
- Form for all business fields from config
- Save button (writes back to config.json)

---

## WHATSAPP INTEGRATION

All WhatsApp features use wa.me links. No API. No approval needed.

### Floating button (every page):
```
https://wa.me/{whatsapp_number}?text={URL-encoded whatsapp_greeting}
```

### Product order button (product detail page):
Built dynamically by variants.js based on selected variant:
```
https://wa.me/{whatsapp_number}?text=Hi%2C+I%27m+interested+in+ordering+{Product+Name}+–+{Variant}.+Can+you+help%3F
```

### Share button (every product card):
```
https://wa.me/?text=Check+out+{Product+Name}%3A+{full_product_url}
```

### Chatbot escalation button (inside chatbot widget):
Shown when user asks about ordering:
```
https://wa.me/{whatsapp_number}?text=Hi%2C+I+was+chatting+with+your+assistant+and+I+need+help+with+an+order.
```

---

## CHATBOT SPECIFICATION (MOCK MODE)

Build the complete chatbot UI and API endpoint. Use mock responses for now.

### API endpoint: POST /api/chat/[slug]
Request body: `{"message": "user message", "history": []}`
Response: `{"reply": "bot response text", "show_whatsapp": false}`

### Mock response logic in chatbot.py:
```python
def mock_response(message: str, config: dict) -> dict:
    message_lower = message.lower()
    products = config.get("products", [])
    faqs = config.get("faqs", [])
    business = config.get("business", {})

    # Price/product queries
    if any(word in message_lower for word in ["price", "cost", "how much", "rate"]):
        product_list = "\n".join([
            f"• {p['name']}: {'Contact for price' if p.get('price_hidden') else f'₹{p[\"price\"]}'}"
            for p in products[:5]
        ])
        return {"reply": f"Here are some of our products:\n{product_list}\n\nFor more details, tap the WhatsApp button below!", "show_whatsapp": True}

    # Order queries
    if any(word in message_lower for word in ["order", "buy", "purchase", "want"]):
        return {"reply": f"I'd love to help you order! Please tap the WhatsApp button below to chat directly with us. We'll get back to you immediately! 😊", "show_whatsapp": True}

    # Delivery/shipping queries
    if any(word in message_lower for word in ["deliver", "ship", "shipping"]):
        return {"reply": "We deliver all across India! Delivery takes 3–5 business days. Tap WhatsApp below for exact delivery info for your area.", "show_whatsapp": True}

    # Hours query
    if any(word in message_lower for word in ["open", "hours", "time", "when"]):
        return {"reply": f"We are open {business.get('hours', 'Mon–Sat, 10AM–8PM')}. You can also WhatsApp us anytime!", "show_whatsapp": False}

    # FAQ matching
    for faq in faqs:
        keywords = faq["question"].lower().split()
        if any(kw in message_lower for kw in keywords if len(kw) > 4):
            return {"reply": faq["answer"], "show_whatsapp": False}

    # Default
    return {"reply": f"Thanks for your message! For the best help, please tap the WhatsApp button below and our team will assist you personally. 😊", "show_whatsapp": True}

# ENGINEER: Replace mock_response() with Claude API call
# Use: anthropic.Anthropic().messages.create(model="claude-sonnet-4-6", ...)
# Pass the full product catalogue and FAQs as system context
# API key from environment: os.environ.get("ANTHROPIC_API_KEY")
```

---

## ADMIN PANEL SPECIFICATION

Simple file-based admin. No database. Reads and writes JSON config directly.

### Authentication (admin_credentials.json):
```json
{
  "zara-perfumes": "admin123",
  "henna-house": "admin456"
}
```
Store slug + password in session cookie. Use FastAPI's built-in session handling.

### Operations (all operate on clients/[slug]/config.json):
- **List products:** Read config, display all products in table
- **Add product:** Form → validate → append to config["products"] → write file
- **Edit product:** Pre-fill form from config → validate → update in config → write file
- **Delete product:** Remove from config["products"] by id → write file
- **Toggle stock:** Flip in_stock boolean → write file (AJAX call, no page reload)
- **Edit settings:** Pre-fill business fields → update config["business"] → write file

### File write function (in config_loader.py):
```python
import json

def save_config(slug: str, config: dict):
    path = f"clients/{slug}/config.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    # Clear cache for this slug so next request reloads
    config_cache.pop(slug, None)
```

---

## DEMO CLIENT CONFIGS

### clients/zara-perfumes/config.json
Perfume business. 6 products across 2 categories (Oud Collection, Floral Collection).
Primary color: #1a1a2e (dark navy). Secondary color: #c9a96e (gold).
Products: Royal Oud 50ml (₹1500, featured), Rose Mist (₹800), Oud Rose (₹2200, bestseller),
Jasmine Dreams (₹950), Lavender Cloud (₹750), Black Amber (₹1800, hidden price).
3 real-looking placeholder image URLs each (use https://via.placeholder.com/600x600/1a1a2e/c9a96e?text=ProductName for now).
FAQs: 4 questions about delivery, returns, authentic ingredients, gift wrapping.

### clients/henna-house/config.json
Henna products business. 5 products across 2 categories (Natural Henna, Accessories).
Primary color: #2d5016 (deep green). Secondary color: #f4a261 (warm orange).
Products: Premium Henna Cone (₹120/piece, min qty 5, featured), Natural Henna Powder 100g (₹280),
Body Art Henna Kit (₹650, bestseller), Glitter Henna Set (₹450), Brown Henna Paste (₹150).
FAQs: 4 questions about natural ingredients, shelf life, how to use, bulk orders.

---

## DESIGN SYSTEM

### Core principle: Mobile first, always
- Test every template at 375px width FIRST
- Bottom navigation-friendly: important buttons always within thumb reach
- Text minimum 14px
- Touch targets minimum 44px height

### Brand color application
Apply client colors via CSS variables throughout:
```css
:root {
  --primary: #1a1a2e;     /* from config */
  --secondary: #e94560;   /* from config */
}
```
Use: `style="background-color: var(--primary)"` and `style="color: var(--secondary)"`

### WhatsApp button: always fixed bottom-right
```html
<a href="https://wa.me/..." 
   class="fixed bottom-6 right-6 z-50 bg-green-500 text-white rounded-full p-4 shadow-lg flex items-center gap-2">
  <svg>...</svg> <!-- WhatsApp icon -->
</a>
```

### Chatbot button: fixed above WhatsApp button
```html
<button onclick="toggleChatbot()"
   class="fixed bottom-24 right-6 z-50 rounded-full p-4 shadow-lg text-white"
   style="background-color: var(--primary)">
  <svg>...</svg> <!-- Chat bubble icon -->
</button>
```

### Product cards
- White background
- 1:1 image aspect ratio (object-cover)
- 8px border radius
- Thin border (#f0f0f0)
- Product name: 14px, semibold
- Price: 16px, primary color, bold
- Out of stock: 50% opacity overlay + "Out of Stock" badge
- Bestseller: golden badge top-left
- Featured: primary color badge top-left

### Color usage
- Page background: white (#ffffff)
- Section backgrounds: very light grey (#f9fafb)
- Hero sections: primary color background, white text
- Buttons: primary color background, white text
- WhatsApp buttons: #25D366 background, white text
- Borders: #e5e7eb (Tailwind gray-200)

---

## JAVASCRIPT FILES

### static/js/gallery.js
```javascript
function switchImage(url) {
  document.getElementById('main-image').src = url;
  document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('ring-2', 'ring-primary'));
  event.target.classList.add('ring-2', 'ring-primary');
}
```

### static/js/variants.js
```javascript
const whatsappNumber = document.getElementById('whatsapp-data').dataset.number;
const productName = document.getElementById('whatsapp-data').dataset.product;
let selectedVariants = {};

function selectVariant(groupName, value, el) {
  selectedVariants[groupName] = value;
  document.querySelectorAll(`[data-group="${groupName}"]`).forEach(btn => {
    btn.classList.remove('bg-primary', 'text-white');
    btn.classList.add('bg-white', 'border');
  });
  el.classList.add('bg-primary', 'text-white');
  el.classList.remove('bg-white', 'border');
  updateWhatsAppLink();
}

function updateWhatsAppLink() {
  const variantStr = Object.entries(selectedVariants).map(([k,v]) => `${k}: ${v}`).join(', ');
  const message = `Hi, I'm interested in ordering ${productName}${variantStr ? ' – ' + variantStr : ''}. Can you help?`;
  const link = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
  document.getElementById('order-whatsapp-btn').href = link;
}
```

### static/js/chatbot.js
```javascript
const slug = document.getElementById('chatbot-data').dataset.slug;
let isOpen = false;
let history = [];

function toggleChatbot() {
  isOpen = !isOpen;
  document.getElementById('chatbot-window').classList.toggle('hidden', !isOpen);
  if (isOpen && history.length === 0) {
    const greeting = document.getElementById('chatbot-data').dataset.greeting;
    appendMessage('bot', greeting);
  }
}

function appendMessage(sender, text) {
  const thread = document.getElementById('chatbot-thread');
  const div = document.createElement('div');
  div.className = sender === 'bot'
    ? 'flex gap-2 mb-3'
    : 'flex gap-2 mb-3 justify-end';
  div.innerHTML = sender === 'bot'
    ? `<div class="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-2 text-sm max-w-xs">${text}</div>`
    : `<div class="text-white rounded-2xl rounded-tr-none px-4 py-2 text-sm max-w-xs" style="background-color:var(--primary)">${text}</div>`;
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
  history.push({role: sender === 'bot' ? 'assistant' : 'user', content: text});
}

async function sendMessage() {
  const input = document.getElementById('chatbot-input');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  appendMessage('user', message);
  const typingDiv = document.createElement('div');
  typingDiv.id = 'typing';
  typingDiv.className = 'flex gap-2 mb-3';
  typingDiv.innerHTML = '<div class="bg-gray-100 rounded-2xl px-4 py-2 text-sm text-gray-400">Typing...</div>';
  document.getElementById('chatbot-thread').appendChild(typingDiv);
  try {
    const res = await fetch(`/api/chat/${slug}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message, history})
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    appendMessage('bot', data.reply);
    if (data.show_whatsapp) {
      const wa = document.getElementById('chatbot-data').dataset.whatsapp;
      const waBtnDiv = document.createElement('div');
      waBtnDiv.className = 'mb-3';
      waBtnDiv.innerHTML = `<a href="https://wa.me/${wa}?text=${encodeURIComponent('Hi, I was chatting with your assistant and need help.')}" target="_blank" class="flex items-center gap-2 bg-green-500 text-white text-sm px-4 py-2 rounded-full w-fit">💬 Chat on WhatsApp</a>`;
      document.getElementById('chatbot-thread').appendChild(waBtnDiv);
    }
  } catch (e) {
    document.getElementById('typing')?.remove();
    appendMessage('bot', 'Sorry, something went wrong. Please WhatsApp us directly!');
  }
}

document.getElementById('chatbot-input')?.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMessage();
});
```

---

## CONFIG LOADER SERVICE

### services/config_loader.py

```python
import json
import os
from typing import Optional

config_cache = {}

def load_config(slug: str) -> Optional[dict]:
    if slug in config_cache:
        return config_cache[slug]
    path = f"clients/{slug}/config.json"
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
    path = f"clients/{slug}/config.json"
    # Remove internal lookup maps before saving
    config_to_save = {k: v for k, v in config.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config_to_save, f, indent=2, ensure_ascii=False)
    config_cache.pop(slug, None)

def list_clients() -> list:
    clients = []
    if not os.path.exists("clients"):
        return clients
    for folder in os.listdir("clients"):
        if folder.startswith("_"):
            continue
        config_path = f"clients/{folder}/config.json"
        if os.path.exists(config_path):
            clients.append(folder)
    return clients
```

---

## REQUIREMENTS.TXT

```
fastapi==0.115.0
uvicorn==0.30.6
jinja2==3.1.4
python-multipart==0.0.9
itsdangerous==2.2.0
```

No other dependencies. No anthropic SDK needed (engineer adds it later).

---

## DEVELOPMENT COMMANDS

```bash
# First time setup (run once):
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt

# Run the app:
uvicorn main:app --reload --port 8000

# Test URLs:
# http://localhost:8000/
# http://localhost:8000/shop/zara-perfumes
# http://localhost:8000/shop/zara-perfumes/product/royal-oud-50ml
# http://localhost:8000/shop/henna-house
# http://localhost:8000/admin/zara-perfumes/login
# http://localhost:8000/health
```

---

## ENGINEER HANDOVER NOTES

When Abinas hands this to the engineer, these are the integration points:

### 1. Replace mock chatbot with Claude API
File: `routers/chatbot.py`
Look for comment: `# ENGINEER: Replace mock_response() with Claude API call`
- Install: `pip install anthropic`
- Add env var: `ANTHROPIC_API_KEY`
- Model: `claude-sonnet-4-6`
- System prompt: inject full product catalogue + FAQs from config

### 2. Add Railway deployment
- Create `railway.toml` with uvicorn start command
- Connect GitHub repo to Railway
- Set env var `ANTHROPIC_API_KEY` in Railway dashboard

### 3. Migrate to database (optional, Stage 1)
- Current: JSON files in `clients/` folder
- Target: PostgreSQL with tables: clients, categories, products, faqs
- Config loader interface stays the same — just change the data source

### 4. Add proper authentication
- Current: hardcoded passwords in admin_credentials.json
- Target: hashed passwords, JWT tokens, or OAuth
- Keep the same session-based approach, just secure it

---

## RULES FOR CLAUDE CODE

1. Read this entire CLAUDE.md before writing anything.
2. Build in the exact order listed in BUILD GOAL.
3. After completing each major file, output: ✅ Built: [filename] — test at [URL]
4. Never stop mid-build to ask questions. Make sensible decisions and keep going.
5. Every template must look excellent at 375px (mobile) BEFORE desktop.
6. Never hardcode client-specific data in Python or HTML. Config only.
7. Commit-worthy code: every file should be complete, not a placeholder.
8. If a URL uses placeholder images (via.placeholder.com), that is acceptable for the demo configs.
9. The chatbot must use mock responses. Do NOT attempt to call the Claude API.
10. When done, output a final summary: files created, URLs to test, what the engineer needs to add.
