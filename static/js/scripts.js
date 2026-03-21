// --- Data Page Search Box ---
const dataSearchBox = document.getElementById('data-search-box');
const dataCategory = document.getElementById('search-category');
const dataSearchButton = document.getElementById('search-button');

function performDataSearch() {
  const query = dataSearchBox.value.trim();
  const category = dataCategory ? dataCategory.value : 'all';

  if (query) {
    // Include both query and category in URL
    window.open(`search_results.html?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}`, '_blank');
  }
}

// Enter key triggers search
if (dataSearchBox) {
  dataSearchBox.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      performDataSearch();
    }
  });
}

// Click on search button triggers search
if (dataSearchButton && dataSearchBox) {
  dataSearchButton.addEventListener('click', performDataSearch);
}


// --- Search Results Page ---
document.addEventListener('DOMContentLoaded', async function() {
  const searchBox = document.getElementById('search-box');
  const resultsContainer = document.getElementById('results-container');
  const resultsCount = document.getElementById('results-count');
  const categorySelect = document.getElementById('search-category');
  const clearButton = document.getElementById('search-clear');

  if (!searchBox || !resultsContainer) return;

  // Normalize strings (remove diacritics + lowercase)
  function normalize(str) {
    return str
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  // Get query from URL
  const urlParams = new URLSearchParams(window.location.search);
  const initialQuery = urlParams.get('q') || '';
  const initialCategory = urlParams.get('category') || 'all';


  searchBox.value = initialQuery;
  if (categorySelect) categorySelect.value = initialCategory;

  // Load JSON
  let searchIndex = [];
  try {
    const res = await fetch('indexes/search_index.json');
    searchIndex = await res.json();
  } catch (err) {
    console.error(err);
    resultsContainer.innerHTML = '<div class="text-danger">Error loading search index.</div>';
    return;
  }

  function performSearch(query, category = 'all', liveFilter = false) {

    const words = normalize(query).split(/\s+/).filter(Boolean);

    resultsContainer.innerHTML = '';

    if (!words.length) {
      resultsCount.textContent = '';
      resultsContainer.innerHTML = '<div class="no-results">Nothing entered, enter a search term above to see results.</div>';
      return;
    }

    const results = searchIndex.filter(item => {

      const name = normalize(item.name);
      const id = normalize(item.id)
      const altNames = (item.alt_names || []).map(a => normalize(a));
      const places = (item.places || []).map(p => normalize(p));
      const searchable = [name, id, ...altNames, ...places].join(" ");

      let matchesQuery;
      if (liveFilter) {
        // match words only at the start of any word
        matchesQuery = words.every(word => {
          const regex = new RegExp(`\\b${word}`, "i"); // word boundary at start
          return regex.test(searchable);
        });
      } else {
        // whole-word match for data-search-box referrals
        matchesQuery = words.every(word => {
          const regex = new RegExp(`\\b${word}\\b`, "i");
          return regex.test(searchable);
        });
      }
      
      const matchesCategory = category === 'all' || item.type.toLowerCase() === category.toLowerCase();
      return matchesQuery && matchesCategory;
    });

    if (!results.length) {
      resultsCount.textContent = '0 results found';
      resultsContainer.innerHTML = '';
      return;
    }

    resultsCount.innerHTML = `<strong>${results.length}</strong> result${results.length !== 1 ? 's' : ''} found`;
    resultsContainer.innerHTML = '';

    // Add top divider
    const topDivider = document.createElement('hr');
    topDivider.className = 'results-divider top-divider';
    resultsContainer.appendChild(topDivider);

    results.forEach((item) => {
      const el = document.createElement('div');
      el.className = 'search-result mb-3';

      const badgeClass = {
        person: "badge-person",
        place: "badge-place",
        work: "badge-work"
      }[item.type.toLowerCase()] || "bg-secondary";

      el.innerHTML = `
        <div>
          <span class="badge ${badgeClass} text-capitalize">${item.type}</span>
        </div>
        <div class="result-title mt-1">
          ${item.name} <span class="text-muted">[${item.id}]</span>
        </div>
        ${item.alt_names && item.alt_names.length ? `
          <div class="result-alt text-muted small">
            Alt names: ${item.alt_names.join(', ')}
          </div>
        ` : ''}
        ${item.places && item.places.length ? `
          <div class="result-places text-muted small">
            Associated Places: ${item.places.join(', ')}
          </div>
        ` : ''}
        <div class="result-link mt-1">
          <a href="${item.url}" target="_blank">View record</a>
        </div>
      `;

      resultsContainer.appendChild(el);

      // Divider after every result
      const divider = document.createElement('hr');
      divider.className = 'results-divider';
      resultsContainer.appendChild(divider);
    });
  }

  performSearch(initialQuery, initialCategory, false);

  searchBox.addEventListener('input', () => {
    performSearch(
      searchBox.value,
      categorySelect ? categorySelect.value : 'all',
      true
    );
  });

  if (categorySelect) {
    categorySelect.addEventListener('change', () => {
      performSearch(
        searchBox.value,
        categorySelect.value,
        true
      );
    });
  }

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      searchBox.value = '';                        
      if (categorySelect) categorySelect.value = 'all'; 
      searchBox.dispatchEvent(new Event('input')); 
      searchBox.focus();                           
    });
  }
});