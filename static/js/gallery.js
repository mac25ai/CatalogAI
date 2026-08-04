// Product page image gallery — tap a thumbnail to swap the main image.

function switchImage(url) {
  document.getElementById('main-image').src = url;
  document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('ring-2', 'ring-primary'));
  if (event && event.target) {
    event.target.classList.add('ring-2', 'ring-primary');
  }
}
