document.addEventListener("DOMContentLoaded", function () {

    let mapObj = null;

    // Attempt to find the Leaflet map object dynamically
    for (let key in window) {
        if (window[key] instanceof L.Map) {
            mapObj = window[key];
            break;
        }
    }

    if (!mapObj) {
        console.warn("Leaflet map object not found. Label zoom toggle will not run.");
        return;
    }

    // -----------------------------
    // Label zoom toggle
    // -----------------------------
    function toggleLabelsByZoom() {
        if (!mapObj) return;

        const zoom = mapObj.getZoom();

        const largeLabels = document.getElementsByClassName('label-large');
        const smallLabels = document.getElementsByClassName('label-small');

        for (let lbl of largeLabels) lbl.style.display = zoom >= 6 ? 'block' : 'none';
        for (let lbl of smallLabels) lbl.style.display = zoom >= 11 ? 'block' : 'none';
    }

    // Initial run (slight delay ensures labels exist in DOM)
    setTimeout(toggleLabelsByZoom, 500);

    // Update labels on zoom change
    mapObj.on('zoomend', toggleLabelsByZoom);

    // -----------------------------
    // Node scaling
    // -----------------------------
    function scaleSize(value, minSize = 12, maxSize = 30) {
        if (value <= 0) return minSize;
        return Math.min(maxSize, minSize + Math.log(value + 1) * 6);
    }

    function updateNodeSizes(mode) {
        let nodes = document.querySelectorAll(".map-node");

        nodes.forEach(node => {
            let size;

            if (mode === "normal") {
                size = 12; // fixed size for normal mode
            } else {
                let value = parseFloat(node.dataset[mode]);
                size = scaleSize(value, 12, 30);
            }

            node.setAttribute("width", size);
            node.setAttribute("height", size);

            // Handle shapes
            let circle = node.querySelector("circle");
            let rect = node.querySelector("rect");
            let polygon = node.querySelector("polygon");

            if (circle) {
                circle.setAttribute("cx", size/2);
                circle.setAttribute("cy", size/2);
                circle.setAttribute("r", (size/2)-1);
            }

            if (rect) {
                rect.setAttribute("width", size-2);
                rect.setAttribute("height", size-2);
            }

            if (polygon) {
                polygon.setAttribute("points", `${size/2},0 ${size},${size} 0,${size}`);
            }
        });

        console.log("Scaling nodes by:", mode);
    }

    // -----------------------------
    // Wait for selector and apply initial scaling
    // -----------------------------
    setTimeout(() => {
        const selector = document.getElementById("scaleSelector");

        if (selector) {
            // Apply scaling when selector changes
            selector.addEventListener("change", function () {
                updateNodeSizes(this.value);
            });
        }

        // Initial scaling on page load
        updateNodeSizes(selector ? selector.value : "works");
    }, 500); // half-second delay, adjust if needed

});