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
      if (query.length < 2) {
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


