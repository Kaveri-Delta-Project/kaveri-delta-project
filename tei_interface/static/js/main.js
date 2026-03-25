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


// Core setup function (can be reused for multiple sections)
function setupEntityLookup(entity, searchInputId, resultsId, hiddenInputId) {
  const input = document.getElementById(searchInputId);
  const resultsBox = document.getElementById(resultsId);
  const hiddenInput = document.getElementById(hiddenInputId);

  if (!input || !resultsBox || !hiddenInput) return;

  let debounceTimer;

  input.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const query = input.value.trim();
      if (query.length < 1) {
        resultsBox.classList.add("d-none");
        return;
      }

      try {
        const response = await fetch(`/api/${entity}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        resultsBox.innerHTML = "";

        data.forEach(item => {
          const option = document.createElement("button");
          option.type = "button";
          option.className = "list-group-item list-group-item-action";
          option.textContent = `${item.name} (${item.xml_id})`;

        option.onclick = () => {
          // Show name + xml_id in the visible input
          input.value = `${item.name} (${item.xml_id})`;
          // Store xml_id in hidden input
          hiddenInput.value = item.xml_id;    
          resultsBox.classList.add("d-none");
        };
        
          resultsBox.appendChild(option);
        });

        resultsBox.classList.toggle("d-none", data.length === 0);
      } catch (err) {
        console.error("Lookup error:", err);
      }
    }, 250); // debounce 250ms
  });

  // Hide dropdown if clicking outside
  document.addEventListener("click", function(e) {
    if (!resultsBox.contains(e.target) && e.target !== input) {
      resultsBox.classList.add("d-none");
    }
  });
}


document.addEventListener("DOMContentLoaded", () => {
  const lookupInputs = document.querySelectorAll("[data-entity-lookup]");

  lookupInputs.forEach(input => {
    const entity = input.dataset.entityLookup;
    const resultsId = input.dataset.resultsId;
    const hiddenId = input.dataset.hiddenId;

    if (entity && resultsId && hiddenId) {
      setupEntityLookup(entity, input.id, resultsId, hiddenId);
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {

  // Only target selects explicitly marked for "Other"
  const selects = document.querySelectorAll("select[data-allow-other='true']");

  selects.forEach(function(select) {
    // skip any selects that also have data-entity-lookup
    if (select.dataset.entityLookup) return;

    const otherInput = document.getElementById(select.id + "_other");
    if (!otherInput) return;

    function toggleOther() {
      if (select.value === "other") {
        otherInput.classList.remove("d-none");
        otherInput.required = true;
      } else {
        otherInput.classList.add("d-none");
        otherInput.required = false;
        otherInput.value = "";
      }
    }

    toggleOther(); // initial check in case "Other" is preselected
    select.addEventListener("change", toggleOther);
  });

});

document.addEventListener("DOMContentLoaded", function () {
  const genreSelect = document.getElementById("genre");
  const commentaryWrapper = document.getElementById("genre_commentary_wrapper");
  const commentaryInput = document.getElementById("genre_commentary");
  const commentaryHidden = document.getElementById("genre_commentary_id");

  if (!genreSelect || !commentaryWrapper || !commentaryInput || !commentaryHidden) return;

  function toggleCommentary() {
    if (genreSelect.value === "commentary") {
      commentaryWrapper.classList.remove("d-none");
      commentaryInput.required = true;
    } else {
      commentaryWrapper.classList.add("d-none");
      commentaryInput.required = false;
      commentaryInput.value = "";
      commentaryHidden.value = "";
    }
  }

  // Initial check in case Commentary is preselected
  toggleCommentary();

  // Update visibility whenever the dropdown changes
  genreSelect.addEventListener("change", toggleCommentary);
});


document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("index-search");
  const rows = document.querySelectorAll(".entity-row");
  const groups = document.querySelectorAll(".letter-group");
  const buttons = document.querySelectorAll('.alphabet button');

  if (!input) return;

  const normalize = str =>
    str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  input.addEventListener("input", () => {
    const query = input.value.trim();
    const q = normalize(query);

    rows.forEach(row => {
      const nameEl = row.querySelector(".entity-name");
      if (!nameEl) return;

      const text = normalize(nameEl.textContent);
      
      const regex = new RegExp(`\\b${q}`);
      const match = regex.test(text);

      row.style.display = match ? "" : "none";
    });

    // Update groups
    groups.forEach(group => {
      const visibleRows = group.querySelectorAll(
        ".entity-row:not([style*='display: none'])"
      );

      const heading = group.querySelector(".letter-heading");
      const noEntries = group.querySelector(".no-entries");

      if (visibleRows.length > 0) {
        group.style.display = "";
        if (heading) heading.style.display = query ? "none" : "";
        if (noEntries) noEntries.style.display = "none";
      } else {
        group.style.display = "none";
      }
    });

    // Disable alphabet buttons during search
    if (query.length > 0) {
      buttons.forEach(btn => btn.disabled = true);
    } else {
      buttons.forEach(btn => btn.disabled = false);

      // Reset view when cleared
      groups.forEach(group => {
        group.style.display = "";
        const heading = group.querySelector(".letter-heading");
        if (heading) heading.style.display = "";
      });

      rows.forEach(row => (row.style.display = ""));
    }
  });
});

