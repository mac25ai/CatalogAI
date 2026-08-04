"""Chatbot API: POST /api/chat/[slug]

Real responses come from Groq (llama-3.3-70b-versatile), grounded in the
client's product catalogue and FAQs via the system prompt. Falls back to
the original keyword-matched mock if GROQ_API_KEY isn't set, so local dev
still works with zero env vars.
"""

import os

from fastapi import APIRouter, HTTPException
from groq import APIStatusError, Groq
from pydantic import BaseModel

from services.config_loader import load_config

router = APIRouter(prefix="/api/chat", tags=["chatbot"])

GROQ_MODEL = "llama-3.3-70b-versatile"
ORDER_KEYWORDS = ("order", "buy", "purchase", "price", "cost", "want")

_groq_client: Groq | None = None


def get_groq_client() -> Groq | None:
    global _groq_client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    if _groq_client is None:
        _groq_client = Groq(api_key=api_key)
    return _groq_client


class ChatRequest(BaseModel):
    message: str
    history: list = []


def format_price(product: dict) -> str:
    if product.get("price_hidden"):
        return "Contact for price"
    return f"₹{product.get('price', 0)}"


def mock_response(message: str, config: dict) -> dict:
    message_lower = message.lower()
    products = config.get("products", [])
    faqs = config.get("faqs", [])
    business = config.get("business", {})

    # Price/product queries
    if any(word in message_lower for word in ["price", "cost", "how much", "rate"]):
        product_list = "\n".join(
            f"• {p['name']}: {format_price(p)}" for p in products[:5]
        )
        return {
            "reply": f"Here are some of our products:\n{product_list}\n\nFor more details, tap the WhatsApp button below!",
            "show_whatsapp": True,
        }

    # Order queries
    if any(word in message_lower for word in ["order", "buy", "purchase", "want"]):
        return {
            "reply": "I'd love to help you order! Please tap the WhatsApp button below to chat directly with us. We'll get back to you immediately! 😊",
            "show_whatsapp": True,
        }

    # Delivery/shipping queries
    if any(word in message_lower for word in ["deliver", "ship", "shipping"]):
        return {
            "reply": "We deliver all across India! Delivery takes 3–5 business days. Tap WhatsApp below for exact delivery info for your area.",
            "show_whatsapp": True,
        }

    # Hours query
    if any(word in message_lower for word in ["open", "hours", "time", "when"]):
        return {
            "reply": f"We are open {business.get('hours', 'Mon–Sat, 10AM–8PM')}. You can also WhatsApp us anytime!",
            "show_whatsapp": False,
        }

    # FAQ matching
    for faq in faqs:
        keywords = faq["question"].lower().split()
        if any(kw in message_lower for kw in keywords if len(kw) > 4):
            return {"reply": faq["answer"], "show_whatsapp": False}

    # Default
    return {
        "reply": "Thanks for your message! For the best help, please tap the WhatsApp button below and our team will assist you personally. 😊",
        "show_whatsapp": True,
    }


def build_system_prompt(config: dict) -> str:
    business = config.get("business", {})
    products = config.get("products", [])
    faqs = config.get("faqs", [])

    product_list = "\n".join(
        f"- {p['name']}: {format_price(p)} | "
        f"{'In Stock' if p.get('in_stock') else 'Out of Stock'} | "
        f"{p.get('short_description', '')}"
        for p in products
    )
    faq_list = "\n".join(f"Q: {f['question']}\nA: {f['answer']}" for f in faqs)

    return f"""You are {business.get('chatbot_name', 'Assistant')}, the AI assistant for {business.get('name')}.
Business hours: {business.get('hours')}
Location: {business.get('location')}

PRODUCTS:
{product_list}

FAQs:
{faq_list}

Rules:
- Answer only questions about this business and its products
- Be warm, helpful, and concise
- For ordering, always direct the customer to WhatsApp
- If you cannot help, say so and suggest WhatsApp
- Respond in the same language the customer uses
- Keep responses under 3 sentences unless listing products"""


def real_response(message: str, config: dict, history: list, client: Groq) -> dict:
    messages = [{"role": "system", "content": build_system_prompt(config)}]
    for turn in history[-6:]:
        role = turn.get("role")
        if role in ("user", "assistant") and turn.get("content"):
            messages.append({"role": role, "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )
    except APIStatusError:
        # Groq outage or rate limit — fall back to the deterministic mock
        # rather than surfacing a 500 to the customer.
        return mock_response(message, config)

    reply = response.choices[0].message.content or ""
    show_whatsapp = any(word in message.lower() for word in ORDER_KEYWORDS)
    return {"reply": reply, "show_whatsapp": show_whatsapp}


@router.post("/{slug}")
async def chat(slug: str, body: ChatRequest):
    config = load_config(slug)
    if config is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    client = get_groq_client()
    if client is None:
        return mock_response(body.message, config)
    return real_response(body.message, config, body.history, client)
