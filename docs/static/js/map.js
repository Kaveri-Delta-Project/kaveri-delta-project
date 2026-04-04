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

    function toggleLabelsByZoom() {
        if (!mapObj) return;

        const zoom = mapObj.getZoom();

        const largeLabels = document.getElementsByClassName('label-large');
        const smallLabels = document.getElementsByClassName('label-small');

        if (!largeLabels.length && !smallLabels.length) return;

        for (let lbl of largeLabels) lbl.style.display = zoom >= 6 ? 'block' : 'none';
        for (let lbl of smallLabels) lbl.style.display = zoom >= 9 ? 'block' : 'none';
    }

    // Initial run (slight delay ensures labels exist in DOM)
    setTimeout(toggleLabelsByZoom, 500);

    // Update labels on zoom change
    mapObj.on('zoomend', toggleLabelsByZoom);
});