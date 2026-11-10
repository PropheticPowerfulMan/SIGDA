"use strict";

(() => {
    const preview = document.getElementById("specimen-preview");
    const controls = document.querySelector(".preview-zoom");
    const reduce = controls.querySelector('[data-preview-zoom="out"]');
    const enlarge = controls.querySelector('[data-preview-zoom="in"]');
    const fit = controls.querySelector('[data-preview-zoom="fit"]');
    const level = controls.querySelector("[data-preview-level]");
    const minimum = 100;
    const maximum = 200;
    const step = 25;
    let zoom = minimum;

    function updateControls() {
        level.textContent = `${zoom} %`;
        reduce.disabled = zoom === minimum;
        fit.disabled = zoom === minimum;
        enlarge.disabled = zoom === maximum;
    }

    function setZoom(value) {
        const centerX = (preview.scrollLeft + preview.clientWidth / 2) / preview.scrollWidth;
        const centerY = (preview.scrollTop + preview.clientHeight / 2) / preview.scrollHeight;
        zoom = Math.min(maximum, Math.max(minimum, value));
        preview.style.setProperty("--preview-scale", zoom / 100);
        preview.scrollTo(
            centerX * preview.scrollWidth - preview.clientWidth / 2,
            centerY * preview.scrollHeight - preview.clientHeight / 2,
        );
        updateControls();
    }

    reduce.addEventListener("click", () => setZoom(zoom - step));
    enlarge.addEventListener("click", () => setZoom(zoom + step));
    fit.addEventListener("click", () => setZoom(minimum));
    updateControls();
    controls.hidden = false;
})();
