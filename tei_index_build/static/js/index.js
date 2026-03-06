const buttons = document.querySelectorAll('.alphabet button');
const groups = document.querySelectorAll('.letter-group');

buttons.forEach(button => {
  button.addEventListener('click', () => {
    const letter = button.dataset.letter;

    // Hide all groups first
    groups.forEach(group => {
      group.classList.remove('active');
    });

    if (letter === "all") {
      // Show every section
      groups.forEach(group => {
        group.classList.add('active');
      });
    } else {
      // Show only selected letter
      const target = document.getElementById('letter-' + letter);
      if (target) {
        target.classList.add('active');
      }
    }
  });
});

document.addEventListener('click', function (e) {
  const header = e.target.closest('.item-header');
  if (!header) return;

  const item = header.parentElement;
  item.classList.toggle('open');
});

window.addEventListener("load", function () {
  const hash = window.location.hash;
  if (!hash) return;

  const target = document.querySelector(hash);
  if (!target) return;

  // Find the letter section containing this entry
  const section = target.closest(".letter-group");
  if (!section) return;

  // Hide all sections
  groups.forEach(group => {
    group.classList.remove("active");
  });

  // Activate the correct one
  section.classList.add("active");

  target.scrollIntoView({ behavior: "smooth", block: "start" });
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
  const searchInput = document.getElementById('index-search');
  const clearButton = document.getElementById('index-search-clear');
  const entries = document.querySelectorAll('.index-entry');

  if (!searchInput) return;

  // Function to filter entries
  const filterEntries = () => {
    const query = searchInput.value.toLowerCase().trim();
    entries.forEach(entry => {
      const title = entry.querySelector('.entry-title');
      if (title) {
        const text = title.textContent.toLowerCase();
        entry.style.display = text.includes(query) ? '' : 'none';
      }
    });
  };

  // Listen to typing in the search input
  searchInput.addEventListener('input', filterEntries);

  // Listen to the clear button
  if (clearButton) {
    clearButton.addEventListener('click', () => {
      searchInput.value = ''; // clear input
      filterEntries();        // reset all entries
      searchInput.focus();    // optional: refocus the input
    });
  }
});

