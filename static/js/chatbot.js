// Chatbot widget — open/close, send messages to /api/chat/[slug],
// render replies, and show a WhatsApp escalation button when the bot asks to.

const chatbotData = document.getElementById('chatbot-data');
const chatbotSlug = chatbotData.dataset.slug;
let chatbotOpen = false;
let chatHistory = [];

function toggleChatbot() {
  chatbotOpen = !chatbotOpen;
  document.getElementById('chatbot-window').classList.toggle('hidden', !chatbotOpen);
  if (chatbotOpen && chatHistory.length === 0) {
    appendMessage('bot', chatbotData.dataset.greeting);
  }
  if (chatbotOpen) {
    document.getElementById('chatbot-input').focus();
  }
}

function appendMessage(sender, text) {
  const thread = document.getElementById('chatbot-thread');
  const div = document.createElement('div');
  div.className = sender === 'bot'
    ? 'flex gap-2 mb-3'
    : 'flex gap-2 mb-3 justify-end';
  const bubble = document.createElement('div');
  if (sender === 'bot') {
    bubble.className = 'bg-gray-100 rounded-2xl rounded-tl-none px-4 py-2 text-sm max-w-xs whitespace-pre-line';
  } else {
    bubble.className = 'text-white rounded-2xl rounded-tr-none px-4 py-2 text-sm max-w-xs whitespace-pre-line';
    bubble.style.backgroundColor = 'var(--primary)';
  }
  bubble.textContent = text; // textContent, never innerHTML — user input stays plain text
  div.appendChild(bubble);
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
  chatHistory.push({ role: sender === 'bot' ? 'assistant' : 'user', content: text });
}

function appendWhatsAppButton() {
  const thread = document.getElementById('chatbot-thread');
  const wa = chatbotData.dataset.whatsapp;
  const message = 'Hi, I was chatting with your assistant and I need help with an order.';
  const div = document.createElement('div');
  div.className = 'mb-3';
  div.innerHTML =
    `<a href="https://wa.me/${wa}?text=${encodeURIComponent(message)}" target="_blank" rel="noopener" ` +
    `class="inline-flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white text-sm font-semibold px-4 py-2.5 rounded-full min-h-[44px]">` +
    `💬 Chat on WhatsApp</a>`;
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
}

function showTyping() {
  const thread = document.getElementById('chatbot-thread');
  const div = document.createElement('div');
  div.id = 'typing';
  div.className = 'flex gap-2 mb-3';
  div.innerHTML = '<div class="bg-gray-100 rounded-2xl px-4 py-2 text-sm text-gray-400">Typing…</div>';
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
}

async function sendMessage() {
  const input = document.getElementById('chatbot-input');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  appendMessage('user', message);
  showTyping();
  try {
    const res = await fetch(`/api/chat/${chatbotSlug}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: chatHistory })
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();
    appendMessage('bot', data.reply);
    if (data.show_whatsapp) {
      appendWhatsAppButton();
    }
  } catch (e) {
    document.getElementById('typing')?.remove();
    appendMessage('bot', 'Sorry, something went wrong. Please WhatsApp us directly!');
    appendWhatsAppButton();
  }
}

document.getElementById('chatbot-input')?.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendMessage();
});
