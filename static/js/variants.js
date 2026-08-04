// Variant selector — highlights the chosen pill per group and rebuilds
// the "Order on WhatsApp" link with the selected variants in the message.

const whatsappData = document.getElementById('whatsapp-data');
const whatsappNumber = whatsappData.dataset.number;
const productName = whatsappData.dataset.product;
let selectedVariants = {};

function selectVariant(groupName, value, el) {
  selectedVariants[groupName] = value;
  document.querySelectorAll(`[data-group="${CSS.escape(groupName)}"]`).forEach(btn => {
    btn.classList.remove('bg-primary', 'text-white');
    btn.classList.add('bg-white', 'border');
  });
  el.classList.add('bg-primary', 'text-white');
  el.classList.remove('bg-white', 'border');
  updateWhatsAppLink();
}

function updateWhatsAppLink() {
  const variantStr = Object.entries(selectedVariants).map(([k, v]) => `${k}: ${v}`).join(', ');
  const message = `Hi, I'm interested in ordering ${productName}${variantStr ? ' – ' + variantStr : ''}. Can you help?`;
  const link = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
  document.getElementById('order-whatsapp-btn').href = link;
}
