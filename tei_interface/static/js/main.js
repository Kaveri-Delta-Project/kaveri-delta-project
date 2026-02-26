// static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
  // Disable browser "helpfulness" for TEI editing
  const inputs = document.querySelectorAll(
    "input[type='text'], input[type='search'], textarea"
  );

  inputs.forEach(el => {
    el.setAttribute("autocomplete", "off");
    el.setAttribute("autocorrect", "off");
    el.setAttribute("autocapitalize", "none");
    el.setAttribute("spellcheck", "false");
  });
});

// ---- Preserve scroll position across form submissions ----
document.addEventListener("DOMContentLoaded", () => {
  // Restore scroll position if we have one
  const savedScroll = sessionStorage.getItem("scrollY");
  if (savedScroll !== null) {
    window.scrollTo(0, parseInt(savedScroll, 10));
    sessionStorage.removeItem("scrollY");
  }

  // Before submitting any form, save scroll position
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", () => {
      sessionStorage.setItem("scrollY", window.scrollY);
    });
  });
});

function toggleEntryForm(formId) {
  const el = document.getElementById(formId);
  if (!el) return;
  el.classList.toggle("d-none");
}

const buttons = document.querySelectorAll('.alphabet button');
const groups = document.querySelectorAll('.letter-group');

buttons.forEach(button => {
  button.addEventListener('click', () => {
    const letter = button.dataset.letter;

    // Show all groups if "all" clicked
    if (letter === 'all') {
      groups.forEach(group => group.style.display = '');
      return;
    }

    // Hide all letter groups
    groups.forEach(group => group.style.display = 'none');

    // Show only the selected letter group
    const target = document.getElementById('letter-' + letter);
    if (target) {
      target.style.display = '';
    }
  });
});

