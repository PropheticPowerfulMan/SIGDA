"use strict";

(() => {
    const button = document.getElementById("menu-toggle");
    const shell = document.querySelector(".app-shell");
    const narrow = window.matchMedia("(max-width: 760px)");

    function storageKey() {
        return narrow.matches ? "sigda-menu-mobile" : "sigda-menu-desktop";
    }

    function setCollapsed(collapsed) {
        shell.dataset.menuCollapsed = String(collapsed);
        button.setAttribute("aria-expanded", String(!collapsed));
        const label = collapsed ? "Développer le menu" : "Replier le menu";
        button.setAttribute("aria-label", label);
        button.title = label;
    }

    function restore() {
        let saved;
        try {
            saved = sessionStorage.getItem(storageKey());
        } catch {
            // Le menu reste utilisable sans stockage de session.
        }
        setCollapsed(saved === null || saved === undefined ? narrow.matches : saved === "true");
    }

    restore();
    button.hidden = false;
    narrow.addEventListener("change", restore);

    button.addEventListener("click", () => {
        const collapsed = shell.dataset.menuCollapsed !== "true";
        setCollapsed(collapsed);
        try {
            sessionStorage.setItem(storageKey(), String(collapsed));
        } catch {
            // Le choix reste actif sur la page en cours.
        }
    });
})();
