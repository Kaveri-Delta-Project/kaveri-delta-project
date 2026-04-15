
function getMap() {
    for (let key in window) {
        if (window[key] instanceof L.Map) {
            return window[key];
        }
    }
    return null;
}


document.addEventListener("DOMContentLoaded", function () {

    const mapObj = getMap();

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



function openPopupAt(lat, lon, zoom = 10) {

    const map = getMap();

    if (!map) {
        console.warn("Leaflet map not found");
        return;
    }

    map.setView([lat, lon], zoom);

    map.eachLayer(function(layer) {
        if (layer.getLatLng && layer.getPopup) {
            const pos = layer.getLatLng();

            if (
                Math.abs(pos.lat - lat) < 0.00001 &&
                Math.abs(pos.lng - lon) < 0.00001
            ) {
                layer.openPopup();
            }
        }
    });
}

window.addEventListener("load", function () {

    if (!window.location.hash) return;

    const coords = window.location.hash.substring(1).split(",");
    if (coords.length !== 2) return;

    const lat = parseFloat(coords[0]);
    const lon = parseFloat(coords[1]);

    if (isNaN(lat) || isNaN(lon)) return;

    function tryOpen(retries = 10) {

        const map = getMap();

        if (!map) {
            if (retries > 0) {
                setTimeout(() => tryOpen(retries - 1), 300);
            }
            return;
        }

        setTimeout(() => {
            openPopupAt(lat, lon);
        }, 500);
    }

    tryOpen();
});
