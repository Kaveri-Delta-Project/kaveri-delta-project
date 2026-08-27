// ============================================================
// Map utilities
// ============================================================

// Find the current Leaflet map instance.
function getMap() {
    // Search the global window object for a Leaflet map instance.
    for (const key in window) {
        if (window[key] instanceof L.Map) {
            return window[key];
        }
    }
    
    // Return null if no Leaflet map instance is found.
    return null;
}


// ============================================================
// Map node labels and scaling
// ============================================================

// Initialise map label visibility and node scaling once the page
// has finished loading.
document.addEventListener("DOMContentLoaded", function () {

    // Find the Leaflet map and all nodes displayed on the map.
    const mapObj = getMap();
    const nodes = document.querySelectorAll(".map-node");

    // Stop if no Leaflet map is available on the page.
    if (!mapObj) {
        console.warn("Leaflet map object not found. Label zoom toggle will not run.");
        return;
    }

    
    // Show or hide map labels according to the current zoom level.
    function toggleLabelsByZoom() {

        const zoom = mapObj.getZoom();

        const largeLabels = document.getElementsByClassName('label-large');
        const smallLabels = document.getElementsByClassName('label-small');

        // Show large labels at medium zoom levels.
        for (const lbl of largeLabels) lbl.style.display = zoom >= 6 ? 'block' : 'none';
        
        // Show small labels only at higher zoom levels.
        for (const lbl of smallLabels) lbl.style.display = zoom >= 11 ? 'block' : 'none';
    }

    // Apply the initial label visibility once the map is ready.
    mapObj.whenReady(toggleLabelsByZoom);

    // Update label visibility whenever the map is zoomed.
    mapObj.on('zoomend', toggleLabelsByZoom);

    
    // Scale node size logarithmically between the minimum and maximum sizes.
    function scaleSize(value, minSize = 12, maxSize = 30) {
        // Return the minimum size for zero or negative values.
        if (value <= 0) return minSize;

        // Increase node size according to the value while capping
        // it at the maximum size.
        return Math.min(maxSize, minSize + Math.log(value + 1) * 6);
    }


    // Update the size and shape of each map node according to the
    // selected scaling mode.
    function updateNodeSizes(mode) {

        nodes.forEach(node => {
            let size;

            // Use a fixed size when normal scaling is selected.
            if (mode === "normal") {
                size = 12;
            } else {
                // Read the value for the selected scaling mode from
                // the node's data attributes.
                const value = parseFloat(node.dataset[mode]);
                size = scaleSize(value);
            }

            // Update the overall dimensions of the node.
            node.setAttribute("width", size);
            node.setAttribute("height", size);

            // Find the shape contained within the node.
            const circle = node.querySelector("circle");
            const rect = node.querySelector("rect");
            const polygon = node.querySelector("polygon");

            // Update circle dimensions to match the new node size.
            if (circle) {
                circle.setAttribute("cx", size / 2);
                circle.setAttribute("cy", size / 2);
                circle.setAttribute("r", (size / 2) - 1);
            }

            // Update rectangle dimensions to match the new node size.
            if (rect) {
                rect.setAttribute("width", size - 2);
                rect.setAttribute("height", size - 2);
            }

            // Update polygon points to match the new node size.
            if (polygon) {
                polygon.setAttribute(
                    "points",
                    `${size / 2},0 ${size},${size} 0,${size}`
                );
            }
        });
    }

    
    // Wait briefly for the map nodes and scale selector to be
    // available before applying the initial scaling.
    setTimeout(() => {
        const selector = document.getElementById("scaleSelector");

        if (selector) {
            // Apply scaling whenever the selected scaling mode changes.
            selector.addEventListener("change", function () {
                updateNodeSizes(this.value);
            });
        }

        // Apply the selected scaling mode when the page first loads.
        // Default to "works" if no selector is present.
        updateNodeSizes(selector ? selector.value : "works");
    }, 500); // half-second delay, adjust if needed

});


// ============================================================
// Map popup and URL hash handling
// ============================================================

// Open the popup for the map node at the specified coordinates.
function openPopupAt(lat, lon, zoom = 10) {

    // Find the current Leaflet map instance. 
    const map = getMap();

    // Stop if no Leaflet map can be found.
    if (!map) {
        console.warn("Leaflet map not found");
        return;
    }

    // Move the map to the specified coordinates and zoom level.
    map.flyTo([lat, lon], zoom, {
      duration: 0.5,
      easeLinearity: 0.25
    });

    // Search all map layers for a node at the specified coordinates.
    map.eachLayer(function(layer) {
        if (layer.getLatLng && layer.getPopup) {
            const pos = layer.getLatLng();

            // Open the popup when the layer's coordinates match
            // the requested latitude and longitude.
            if (
                Math.abs(pos.lat - lat) < 0.00001 &&
                Math.abs(pos.lng - lon) < 0.00001
            ) {
                layer.openPopup();
            }
        }
    });
}


// Handle map coordinates supplied through the URL hash.
function handleMapHash() {

    // Stop if no hash is present in the URL.
    if (!window.location.hash) return;

    // Remove the "#" and split the hash into latitude and longitude.
    const coords = window.location.hash.substring(1).split(",");
    if (coords.length !== 2) return;

    // Convert the coordinate values from strings to numbers.
    const lat = parseFloat(coords[0]);
    const lon = parseFloat(coords[1]);

    // Stop if either coordinate is not a valid number.
    if (isNaN(lat) || isNaN(lon)) return;

    // Find the Leaflet map instance currently loaded on the page.
    const map = getMap();

    // Wait and try again if the map has not been created yet.
    if (!map) {
        setTimeout(handleMapHash, 200);
        return;
    }

    // Wait until the map is ready before moving to the coordinates
    // and opening the corresponding popup.
    map.whenReady(() => {
        openPopupAt(lat, lon);
    });
}


// Handle the map hash on page load and whenever the URL hash changes.
window.addEventListener("load", handleMapHash);
window.addEventListener("hashchange", handleMapHash);
