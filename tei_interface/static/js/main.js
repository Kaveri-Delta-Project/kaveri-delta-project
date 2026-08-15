// static/js/main.js


// ============================================================
// Page initialisation
//

document.addEventListener("DOMContentLoaded", () => {
  initEditingInputs();
  initScrollRestoration();
  initAlphabetFilter();
  initEntityLookups();
  initOtherSelects();
  initGenreCommentary();
  initIndexSearch();

  updateEntityCount();
});


// ============================================================
// Disable browser "helpfulness" for TEI editing
// ============================================================

function initEditingInputs() {
  const inputs = document.querySelectorAll(
    "input[type='text'], input[type='search'], textarea"
  );

  // Prevent browser corrections and suggestions from altering text.
  inputs.forEach(el => {
    el.setAttribute("autocomplete", "off");
    el.setAttribute("autocorrect", "off");
    el.setAttribute("autocapitalize", "none");
    el.setAttribute("spellcheck", "false");
  });
}


// ============================================================
// Preserve scroll position across form submissions
// ============================================================

function initScrollRestoration() {
  
  // Retrieve the scroll position saved before the previous form submission.
  const savedScroll = sessionStorage.getItem("scrollY");

  // If a position was saved, restore the page to that vertical position.
  // scrollY represents the number of pixels the page has been scrolled vertically.
  if (savedScroll !== null) {
    window.scrollTo(0, parseInt(savedScroll, 10));
    sessionStorage.removeItem("scrollY");
  }

  // Clear the loading state when the page finishes loading.
  document.body.classList.remove("loading");

  // Add a submit listener to every form on the page.
  // This saves the user's current position before the page reloads.
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", () => {
      // Store the current vertical scroll position so it can be
      // restored after the form submission and page reload.
      sessionStorage.setItem("scrollY", window.scrollY);

      // Add the loading state shortly after submission.
      // The short delay allows the form submission to begin first.
      setTimeout(() => {
        document.body.classList.add("loading");
      }, 300);
    });
  });
}


// ============================================================
// Entity count
// ============================================================

// Count the total number of entity rows and how many are currently visible.
function countEntityEntries() {
  const rows = document.querySelectorAll(".entity-row");

  let visible = 0;
  const total = rows.length;

  rows.forEach(row => {
    // A row is counted as visible only if it is actually displayed
    // and does not have the d-none class applied.
    const isVisible =
      row.offsetParent !== null &&
      !row.classList.contains("d-none");

    if (isVisible) {
      visible++;
    }
  });

  // Return both values so they can be used by updateEntityCount().
  return { visible, total };
}


// Update the entry-count element with the current visible and total counts.
function updateEntityCount() {
  const el = document.getElementById("entry-count");

  // Do nothing if this page does not contain an entry-count element.
  if (!el) return;

  const { visible, total } = countEntityEntries();

  // Display the number of visible entries alongside the total number of entries.
  el.innerHTML =
    `<strong>${visible}</strong> of <strong>${total}</strong> entries`;
}


// ============================================================
// Entry forms
// ============================================================

// Toggle the visibility of an entry form.
// If the form is visible, hide it; if it is hidden, show it.
function toggleEntryForm(formId) {
  const el = document.getElementById(formId);

  // Do nothing if the specified form cannot be found.
  if (!el) return;

  el.classList.toggle("d-none");
}


// Show an entry form without affecting its current state if it is already visible.
function showEntryForm(formId) {
  const el = document.getElementById(formId);

  // Do nothing if the specified form cannot be found.
  if (!el) return;

  el.classList.remove("d-none");
}


// ============================================================
// Alphabet filter
// ============================================================


// Store the currently selected alphabet filter.
// "all" means that no letter filter is active.
let activeLetter = "all";

function initAlphabetFilter() {
  // Find the alphabet filter buttons and the groups of entries
  // that correspond to each letter.
  const buttons = document.querySelectorAll(".alphabet button");
  const groups = document.querySelectorAll(".letter-group");

  // Add a click listener to each alphabet button.
  buttons.forEach(button => {
    button.addEventListener("click", () => {
      
      // Store the letter selected by the user.
      activeLetter = button.dataset.letter;

      // If "all" is selected, show every letter group.
      if (activeLetter === "all") {
        groups.forEach(group => {
          group.style.display = "";
        });

        // Update the entry count to reflect the current filter.
        updateEntityCount();
        return;
      }

      // Hide all letter groups before showing the selected one.
      groups.forEach(group => {
        group.style.display = "none";
      });

      // Find the group whose ID corresponds to the selected letter.
      const target = document.getElementById(
        "letter-" + activeLetter
      );

      // Show the selected letter group if it exists.
      if (target) {
        target.style.display = "";
      }

      // Update the entry count to reflect the current filter.
      updateEntityCount();
    });
  });
}

// ============================================================
// Entity lookup/autocomplete
// ============================================================

function setupEntityLookup(
  entity,
  searchInputId,
  resultsId,
  hiddenInputId
) {
  
  // Find the visible search input, the results dropdown,
  // and the hidden input used to store the selected XML ID.
  const input = document.getElementById(searchInputId);
  const resultsBox = document.getElementById(resultsId);
  const hiddenInput = document.getElementById(hiddenInputId);

  // Stop if any of the required elements are missing.
  if (!input || !resultsBox || !hiddenInput) return;

  // Store the pending search timeout so it can be cancelled
  // if the user continues typing.
  let debounceTimer;
  
  // Run the lookup whenever the user changes the search input.
  input.addEventListener("input", function () {
    // Cancel the previous pending lookup.
    clearTimeout(debounceTimer);

    // Wait briefly before searching so that rapid typing does not
    // send a request for every individual keystroke.
    debounceTimer = setTimeout(async () => {
      const query = input.value.trim();

      // Hide the results if the search box is empty.
      if (query.length < 1) {
        resultsBox.classList.add("d-none");
        return;
      }

      try {
        // Request matching entities from the relevant API endpoint.
        const response = await fetch(
          `/api/${entity}/search?q=${encodeURIComponent(query)}`
        );

        // Convert the JSON response into a JavaScript value.
        const data = await response.json();

        // Clear any results from the previous search.
        resultsBox.innerHTML = "";

        // Create a button for each matching entity.
        data.forEach(item => {
          const option = document.createElement("button");

          option.type = "button";
          option.className =
            "list-group-item list-group-item-action";

          // Display the entity name and XML ID to the user.
          option.textContent =
            `${item.name} (${item.xml_id})`;

          // When a result is selected, populate the visible input
          // and store the XML ID in the hidden form field.
          option.addEventListener("click", () => {
            // Show name + xml_id in the visible input.
            input.value =
              `${item.name} (${item.xml_id})`;
            
            // Store only the xml_id in the hidden input.
            hiddenInput.value = item.xml_id;

            // Add the result button to the dropdown.
            resultsBox.classList.add("d-none");
          });

          resultsBox.appendChild(option);
        });

        // Hide the dropdown when there are no matching results;
        // otherwise, make it visible.
        resultsBox.classList.toggle(
          "d-none",
          data.length === 0
        );

      // Log any error that occurs while contacting the API.
      } catch (err) {
        console.error("Lookup error:", err);
      }
    }, 250);
  });

  // Hide the results dropdown when the user clicks elsewhere on the page.
  document.addEventListener("click", event => {
    if (
      !resultsBox.contains(event.target) &&
      event.target !== input
    ) {
      resultsBox.classList.add("d-none");
    }
  });
}


// Find and initialise every input field that has been configured
// for entity lookup by the data-entity-lookup attribute.
function initEntityLookups() {
  
  // Find all inputs marked as entity lookup fields.
  const lookupInputs =
    document.querySelectorAll("[data-entity-lookup]");

  // Initialise each lookup field individually.
  lookupInputs.forEach(input => {
    
    // Read the entity type and the IDs of the results and hidden
    // input elements from the input's data-* attributes.
    const entity = input.dataset.entityLookup;
    const resultsId = input.dataset.resultsId;
    const hiddenId = input.dataset.hiddenId;

    // Only initialise the lookup when all required configuration
    // values are present.
    if (entity && resultsId && hiddenId) {
      setupEntityLookup(
        entity,
        input.id,
        resultsId,
        hiddenId
      );
    }
  });
}

// ============================================================
// "Other" select fields
// ============================================================

function initOtherSelects() {
  // Find select fields that allow the user to enter a custom value.
  const selects =
    document.querySelectorAll(
      "select[data-allow-other='true']"
    );

  selects.forEach(select => {
    // Skip selects that are handled by the entity lookup system.
    if (select.dataset.entityLookup) return;

    // Find the text input associated with this select.
    const otherInput =
      document.getElementById(
        select.id + "_other"
      );

    if (!otherInput) return;

    // Show or hide the custom-value input according to the selection.
    function toggleOther() {
      if (select.value === "Other") {
        otherInput.classList.remove("d-none");
        otherInput.required = true;
      } else {
        otherInput.classList.add("d-none");
        otherInput.required = false;
        otherInput.value = "";
      }
    }

    // Set the correct initial state when the page loads.
    toggleOther();

    // Update the input whenever the user changes the selection.
    select.addEventListener(
      "change",
      toggleOther
    );
  });
}

// ============================================================
// Genre commentary
// ============================================================

function initGenreCommentary() {
  // Find the genre select and the elements used for commentary.
  const genreSelect =
    document.getElementById("genre");

  const commentaryWrapper =
    document.getElementById(
      "genre_commentary_wrapper"
    );

  const commentaryInput =
    document.getElementById(
      "genre_commentary"
    );

  const commentaryHidden =
    document.getElementById(
      "genre_commentary_id"
    );

   // Stop if the required elements are not present on this page.
  if (
    !genreSelect ||
    !commentaryWrapper ||
    !commentaryInput ||
    !commentaryHidden
  ) {
    return;
  }

  // Show or hide the commentary field according to the selected genre.
  function toggleCommentary() {
    if (genreSelect.value === "Commentary") {
      commentaryWrapper.classList.remove("d-none");
      commentaryInput.required = true;
    } else {
      commentaryWrapper.classList.add("d-none");
      commentaryInput.required = false;
      commentaryInput.value = "";
      commentaryHidden.value = "";
    }
  }

  // Set the correct initial state when the page loads.
  toggleCommentary();

  // Update the commentary field whenever the genre selection changes.
  genreSelect.addEventListener(
    "change",
    toggleCommentary
  );
}


// ============================================================
// Index search
// ============================================================

// Handle live filtering of the already-loaded entity index.
// This responds to changes in the search input and updates
// which entity rows and alphabet groups are visible.

function initIndexSearch() {
  // Find the search input, entity rows, letter groups,
  // and alphabet filter buttons used by the entity index page.
  const input =
    document.getElementById("index-search");

  const rows =
    document.querySelectorAll(".entity-row");

  const groups =
    document.querySelectorAll(".letter-group");

  const buttons =
    document.querySelectorAll(".alphabet button");

  // Stop if this page does not contain the index search.
  if (!input) return;

  // Normalise text so searches are case-insensitive and
  // do not distinguish between accented and unaccented characters.
  const normalize = str =>
    str
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

  // Filter the index whenever the search input changes.
  input.addEventListener("input", () => {
    const query = input.value.trim();
    const q = normalize(query);

    // Check each entity row against the current search and
    // the currently selected alphabet filter.
    rows.forEach(row => {
      const nameEl =
        row.querySelector(".entity-name");

      if (!nameEl) return;

      // Get the entity's name from the row and normalise it
      // in the same way as the user's search text.
      const text =
        normalize(nameEl.textContent);

      // Match the search at a word boundary so that the search
      // term must begin at the start of a word within the name.
      const regex =
        new RegExp(`\\b${escapeRegExp(q)}`);

      // Treat every row as a match when the search is empty;
      // otherwise, test the entity name against the search pattern.
      const match =
        q.length === 0 || regex.test(text);

      // Determine which alphabet group contains this row.
      const rowLetter =
        row
          .closest(".letter-group")
          ?.id
          ?.replace("letter-", "");

      // The row is within the current alphabet filter when
      // "all" is selected or its group matches the active letter.
      const inScope =
        activeLetter === "all" ||
        rowLetter === activeLetter;

      // Only show rows that satisfy both the search and
      // alphabet-filter conditions.
      const visible =
        match && inScope;

      row.classList.toggle(
        "d-none",
        !visible
      );
    });

    // Update each alphabet group after the individual rows
    // have been filtered, hiding groups with no matching rows.
    groups.forEach(group => {
      const visibleRows =
        group.querySelectorAll(
          ".entity-row:not(.d-none)"
        );

      const heading =
        group.querySelector(".letter-heading");

      const noEntries =
        group.querySelector(".no-entries");

      // Hide the entire group when none of its entity rows match.
      group.style.display =
        visibleRows.length ? "" : "none";

      // Keep the letter heading visible for displayed groups.
      if (heading) {
        heading.style.display = "";
      }

      // Show the "No entries" message when the group has
      // no matching entity rows.
      if (noEntries) {
        noEntries.style.display =
          visibleRows.length ? "none" : "";
      }
    });

    // Disable the alphabet buttons while a search is active,
    // since the search results are currently controlling the list.
    if (query.length > 0) {
      buttons.forEach(button => {
        button.disabled = true;
      });
    } else {
      // Re-enable the alphabet buttons when the search is cleared.
      buttons.forEach(button => {
        button.disabled = false;
      });

      // Restore the normal index view before reapplying
      // the currently selected alphabet filter.
      groups.forEach(group => {
        group.style.display = "";

        const heading =
          group.querySelector(".letter-heading");

        if (heading) {
          heading.style.display = "";
        }
      });

      rows.forEach(row => {
        row.classList.remove("d-none");
      });

      // Reapply the active alphabet filter so clearing the
      // search does not lose the user's previous letter selection.
      buttons.forEach(button => {
        if (
          button.dataset.letter === activeLetter
        ) {
          button.click();
        }
      });
    }

    // Refresh the visible/total entry count after filtering.    
    updateEntityCount();
  });
}


// Escape special characters before using user input in a RegExp.
// This ensures that characters such as ".", "*", "?", or "("
// are treated as ordinary search characters rather than as
// special RegExp instructions.
function escapeRegExp(value) {
  return value.replace(
    /[.*+?^${}()|[\]\\]/g,
    "\\$&"
  );
}


// ============================================================
// Edit forms
// ============================================================

// Populate the edit form with the existing values of an item.
// Supports both single-value and multiple-field edit sections.
// Records which item is being edited and displays the edit state.

function editItem(sectionName, index, values) {
  
  // Convert underscores to hyphens so the section name matches
  // the IDs used by the edit form elements.
  const baseId =
    sectionName.replace(/_/g, "-");

  // Find the field used to store the index of the item
  // currently being edited.
  const editIndexEl =
    document.getElementById(
      `${baseId}-edit-index`
    );

  // Find the label used to indicate that the form is in edit mode.
  const editLabelEl =
    document.getElementById(
      `${baseId}-edit-label`
    );

  // Stop if the edit-index field cannot be found.
  if (!editIndexEl) {
    console.warn(
      `Edit index element not found for section: ${sectionName}`
    );
    return;
  }

  // If values is a string, the section has a single editable field.
  if (typeof values === "string") {
    const inputEl =
      document.getElementById(sectionName);

    // Stop if the expected input field cannot be found.
    if (!inputEl) {
      console.warn(
        `Input element not found for section: ${sectionName}`
      );
      return;
    }

    // Put the existing value into the input field.
    inputEl.value = values;
  }

  // If values is an object, it contains multiple field/value pairs.
  else if (
    typeof values === "object" &&
    values !== null
  ) {
    
    // Process each field/value pair in the object.
    Object.entries(values).forEach(
      ([key, val]) => {
        
        // Find the form element whose ID matches the field name.
        const el =
          document.getElementById(key);

        if (el) {

          // Put the existing value into the input field.
          el.value = val;
        
        } else {

          // Warn if a supplied field does not exist in the form.
          console.warn(
            `Element not found: ${key}`
          );
        }
      }
    );
  }

  // Store the index of the item being edited so that the
  // submitted form knows which existing item to update.
  editIndexEl.value = index;

  // Show the edit label to indicate that the form is in edit mode.
  if (editLabelEl) {
    editLabelEl.classList.remove("d-none");
  }
}


// Reset an edit form when the user cancels editing.
// Clears the editable fields and removes the current edit index.
// Hides the edit label so the form returns to its normal state.

function resetEditForm(sectionName) {
  
  // Convert underscores to hyphens so the section name matches
  // the IDs used by the form elements.
  const baseId =
    sectionName.replace(/_/g, "-");

  // Find the form for this section.
  const formEl =
    document.getElementById(
      `${baseId}-form`
    );

  // Find the field used to store the index of the item
  // currently being edited.
  const editIndexEl =
    document.getElementById(
      `${baseId}-edit-index`
    );

  // Find the label used to indicate that the form is in edit mode.
  const editLabelEl =
    document.getElementById(
      `${baseId}-edit-label`
    );

  // Stop if the form cannot be found.
  if (!formEl) return;

  // Find the part of the form containing the editable fields.
  const inputsWrapper =
    formEl.querySelector(".editable-fields");

  // Find all editable input, select, and textarea elements
  // within the form and reset their values or checked state.  
  if (inputsWrapper) {
    inputsWrapper
      .querySelectorAll(
        "input, select, textarea"
      )
      .forEach(el => {
        
        // Uncheck checkboxes and radio buttons.
        if (
          el.type === "checkbox" ||
          el.type === "radio"
        ) {
          el.checked = false;
        
        // Clear the value of other form fields.
        } else {
          el.value = "";
        }
      });
  }

  // Clear the index of the item currently being edited.
  if (editIndexEl) {
    editIndexEl.value = "";
  }

  // Hide the edit label so the form is no longer shown
  // as being in edit mode.
  if (editLabelEl) {
    editLabelEl.classList.add("d-none");
  }
}



