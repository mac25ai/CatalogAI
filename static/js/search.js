// Live search filtering on the search results page.
// The server renders the results for the submitted query; typing in the box
// filters those results instantly without a round trip. Pressing Enter still
// submits the form for a fresh full-catalogue search.

const searchInput = document.getElementById('search-input');
const resultsGrid = document.getElementById('search-results');

if (searchInput && resultsGrid) {
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    let visible = 0;
    resultsGrid.querySelectorAll('.search-result').forEach(card => {
      const haystack = `${card.dataset.name} ${card.dataset.tags}`;
      const match = q === '' || q.split(/\s+/).every(term => haystack.includes(term));
      card.classList.toggle('hidden', !match);
      if (match) visible++;
    });
    const countEl = document.getElementById('result-count');
    if (countEl && q !== '') {
      countEl.innerHTML =
        `<span class="font-semibold">${visible}</span> product${visible !== 1 ? 's' : ''} shown — press Enter to search the full catalogue`;
    }
  });
}
