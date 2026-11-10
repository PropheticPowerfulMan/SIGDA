"use strict";

(() => {
    const button = document.querySelector("[data-print-specimen]");
    const preview = document.querySelector(".preview-scroll img");
    const error = document.querySelector("[data-print-error]");
    button.hidden = false;

    button.addEventListener("click", async () => {
        error.hidden = true;
        if (!preview.complete || !preview.naturalWidth) {
            try {
                await preview.decode();
            } catch {
                error.hidden = false;
                return;
            }
        }
        window.print();
    });
})();
