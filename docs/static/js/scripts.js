// --- Data Search Box (homepage / main search) ---
const dataSearchBox = document.getElementById('data-search-box');
const dataCategory = document.getElementById('search-category');
const dataSearchButton = document.getElementById('search-button');
const dropdown = document.getElementById('autocomplete-dropdown');

let searchIndex = [];

// Load search index
fetch('indexes/search_index.json')
  .then(res => res.json())
  .then(data => { searchIndex = data; })
  .catch(err => console.error('Error loading search index:', err));

// Normalize helper
function normalize(str) {
  return str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

// Get dropdown matches
function getDropdownMatches(query, category = 'all') {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (!words.length) return [];

  return searchIndex
    .filter(item => {
      const searchable = normalize(item.name)

      const matchesQuery = words.every(word => {
        const regex = new RegExp(`\\b${word}`, "i"); // word boundary at start
        return regex.test(searchable);
      });
      const matchesCategory =
        category === 'all' ||
        item.type.toLowerCase() === category.toLowerCase();
      return matchesQuery && matchesCategory;
    })
    .slice(0, 10);
}

// Render dropdown
function renderDropdown(matches) {
  dropdown.innerHTML = '';

  if (!matches.length) {
    dropdown.style.display = 'none';
    return;
  }

  const header = document.createElement('div');
  header.className = 'list-group-item disabled';
  header.textContent = 'Suggested searches..';
  dropdown.appendChild(header);

  matches.forEach(item => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'list-group-item list-group-item-action';
    btn.textContent = `${item.name}`;

    btn.addEventListener('click', () => {
      dataSearchBox.value = item.name;
      dropdown.style.display = 'none';
    });

    dropdown.appendChild(btn);
  });

  dropdown.style.display = 'block';
}

// Live filtering
if (dataSearchBox) {
  dataSearchBox.addEventListener('input', () => {
    const matches = getDropdownMatches(
      dataSearchBox.value,
      dataCategory ? dataCategory.value : 'all'
    );
    renderDropdown(matches);
  });

  // Enter key triggers full search
  dataSearchBox.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      performDataSearch();
    }
  });
}

// Hide dropdown when clicking outside
document.addEventListener('click', (e) => {
  if (
    dropdown &&
    !dropdown.contains(e.target) &&
    e.target !== dataSearchBox
  ) {
    dropdown.style.display = 'none';
  }
});

// Perform full search
function performDataSearch() {
  const query = dataSearchBox.value.trim();
  const category = dataCategory ? dataCategory.value : 'all';

  if (query) {
    window.open(
      `search_results.html?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}`,
      '_blank'
    );
  }
}

// Search button click
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

  function performSearch(query, category = 'all') {
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

      // Start-of-word match for every search
      const matchesQuery = words.every(word => {
        const regex = new RegExp(`\\b${word}`, "i");
        return regex.test(searchable);
      });

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
            Alternative Names: ${item.alt_names.join(', ')}
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
    performSearch(searchBox.value, categorySelect?.value || 'all');
  });

  if (categorySelect) {
    categorySelect.addEventListener('change', () => {
      performSearch(searchBox.value, categorySelect.value);
    });
  }

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      searchBox.value = '';
      if (categorySelect) categorySelect.value = 'all';
      performSearch('', categorySelect?.value || 'all');
      searchBox.focus();
    });
  }
});