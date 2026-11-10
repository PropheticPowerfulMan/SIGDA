"use strict";

(() => {
    const button = document.getElementById("theme-toggle");
    if (!button) return;

    const root = document.documentElement;
    const label = button.querySelector("[data-theme-label]");
    const sun = button.querySelector('[data-theme-icon="sun"]');
    const moon = button.querySelector('[data-theme-icon="moon"]');
    const preferenceKey = "sigda-theme";

    function applyTheme(theme) {
        const light = theme === "light";
        root.dataset.theme = theme;
        label.textContent = light ? "Sombre" : "Clair";
        button.setAttribute("aria-label", light ? "Activer le thème sombre" : "Activer le thème clair");
        sun.toggleAttribute("hidden", light);
        moon.toggleAttribute("hidden", !light);
    }

    let savedTheme;
    try {
        savedTheme = localStorage.getItem(preferenceKey);
    } catch {
        // Le thème reste utilisable lorsque le navigateur bloque le stockage.
    }
    applyTheme(savedTheme === "light" ? "light" : "dark");
    button.hidden = false;

    button.addEventListener("click", () => {
        const theme = root.dataset.theme === "light" ? "dark" : "light";
        applyTheme(theme);
        try {
            localStorage.setItem(preferenceKey, theme);
        } catch {
            // Le changement reste actif pour la page en cours.
        }
    });
})();
