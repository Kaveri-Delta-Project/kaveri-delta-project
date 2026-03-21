document.addEventListener('DOMContentLoaded', () => {
  const buttons = document.querySelectorAll('.alphabet button');
  const entries = document.querySelectorAll('.letter-entry');
  const entriesIndex = document.querySelectorAll('.index-entry')

  const showAllEntries = () => {
    const searchInput = document.getElementById("index-search");
    if (searchInput) searchInput.value = "";

    // Show all entries (both letter and search entries)
    const allEntries = document.querySelectorAll('.letter-entry');
    allEntries.forEach(entry => {
      entry.style.display = 'block';
      entry.classList.remove('open');
    });

    const allEntriesIndex = document.querySelectorAll('.index-entry');
    allEntriesIndex.forEach(entry => {
      entry.style.display = 'block';
      entry.classList.remove('open');
    });

    // Remove highlight from all alphabet buttons
    const buttons = document.querySelectorAll('.alphabet button');
    buttons.forEach(btn => btn.classList.remove('active-letter'));

    // Reset active groups
    const groups = document.querySelectorAll('.letter-group');
    groups.forEach(group => group.classList.remove('active'));
  };

  // Show all entries first
  showAllEntries();

  // --- Alphabet button clicks ---
  buttons.forEach(button => {
    button.addEventListener('click', () => {
      const letter = button.dataset.letter;

    const searchInput = document.getElementById("index-search");
    if (searchInput) {
      searchInput.value = "";
      searchInput.dispatchEvent(new Event("input")); // reset live search
    }

    buttons.forEach(btn => btn.classList.remove('active-letter', 'active-all'));

    if (letter === 'all') {
      button.classList.add('active-all');
      showAllEntries();
      return;
      } else {
        button.classList.add('active-letter');
      }

    buttons.forEach(btn => btn.classList.remove('active-letter'));
    button.classList.add('active-letter');

    entries.forEach(entry => {
      if (entry.dataset.letter && entry.dataset.letter.toUpperCase() === letter.toUpperCase()) {
        entry.style.display = 'block';
      } else {
        entry.style.display = 'none';
      }
    });

    entriesIndex.forEach(entry => {
      entry.style.display = 'block';
      entry.classList.remove('open');
    });

    });
  });

  function focusHashTarget() {
    const hash = window.location.hash;
    if (!hash) return;

    const target = document.querySelector(hash);
    if (target && (target.classList.contains('index-entry') || target.classList.contains('letter-entry'))) {

      showAllEntries();

      target.style.display = 'block';
      target.classList.add('open');

      const section = target.closest('.letter-group');
      if (section) {
        document.querySelectorAll('.letter-group').forEach(g => g.classList.remove('active'));
        section.classList.add('active');
      }

      setTimeout(() => {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.classList.add('hash-highlight');
        setTimeout(() => target.classList.remove('hash-highlight'), 2500);

        history.replaceState(null, null, window.location.pathname + window.location.search);

      }, 50);
    }
  }

  focusHashTarget();
});


document.addEventListener('click', function (e) {
  const header = e.target.closest('.item-header');
  if (!header) return;

  const item = header.parentElement;
  item.classList.toggle('open');
});

document.addEventListener('click', function (e) {
  const header = e.target.closest('.entry-header');
  if (!header) return;

  const item = header.parentElement;
  const details = item.querySelector('.item-details');
  if (!details) return;

  const isEmpty = details.children.length === 0;

  if (isEmpty) {
    // Prevent duplicate messages
    if (!details.querySelector('.temp-no-metadata')) {
      const msg = document.createElement('div');
      msg.className = 'temp-no-metadata';
      msg.textContent = 'No metadata';
      details.appendChild(msg);

      // Open panel so message is visible
      item.classList.add('open');

      // Remove after 2 seconds and close again
      setTimeout(() => {
        msg.remove();
        item.classList.remove('open');
      }, 2000);
    }
    return;
  }

  // Normal toggle if metadata exists
  item.classList.toggle('open');
});


document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("index-search");
  const entries = document.querySelectorAll(".index-entry");

  if (!searchInput) return;

  const normalizeText = (text) =>
    text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  const performSearch = () => {
    const rawQuery = searchInput.value.trim();

    if (rawQuery === "") {
      entries.forEach(entry => entry.style.display = "");
      return;
    }

    const query = normalizeText(rawQuery);
    const regex = new RegExp(`\\b${query}`, "i");

    entries.forEach(entry => {
      const title = entry.querySelector(".entry-title");
      if (!title) return;

      const text = normalizeText(title.textContent);
      entry.style.display = regex.test(text) ? "" : "none";
    });
  };

  // Live filtering as the user types
  searchInput.addEventListener("input", performSearch);

  const clearButton = document.getElementById("search-clear");
  if (searchInput && clearButton) {
    clearButton.addEventListener("click", () => {
      searchInput.value = "";
      searchInput.dispatchEvent(new Event("input")); // trigger live filtering
      searchInput.focus();

      // Also reset alphabet buttons
      const buttons = document.querySelectorAll('.alphabet button');
      buttons.forEach(btn => btn.classList.remove('active-letter', 'active-all'));

      // Show all entries again
      const allEntries = document.querySelectorAll('.letter-entry, .index-entry');
      allEntries.forEach(entry => {
        entry.style.display = 'block';
        entry.classList.remove('open');
      });

      // Reset groups
      document.querySelectorAll('.letter-group').forEach(group => group.classList.remove('active'));
    });
  }
});


