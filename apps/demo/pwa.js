"use strict";

(() => {
    if (!window.isSecureContext || !("serviceWorker" in navigator)) return;

    const workerUrl = document.currentScript?.dataset.worker || "./sw.js";
    navigator.serviceWorker.register(workerUrl).catch((error) => {
        console.warn("Installation de SIGDA indisponible.", error);
    });

    const button = document.querySelector("[data-install-button]");
    const help = document.querySelector("[data-install-help]");
    if (!button || !help) return;

    const standalone = window.matchMedia("(display-mode: standalone)");
    if (standalone.matches || navigator.standalone === true) return;

    let promptEvent = null;
    function showHelp(visible) {
        help.hidden = !visible;
        button.setAttribute("aria-expanded", String(visible));
    }

    window.addEventListener("beforeinstallprompt", (event) => {
        event.preventDefault();
        promptEvent = event;
    });

    window.addEventListener("appinstalled", () => {
        promptEvent = null;
        showHelp(false);
        button.hidden = true;
    });

    button.addEventListener("click", async () => {
        if (!promptEvent) {
            showHelp(help.hidden);
            return;
        }

        const availablePrompt = promptEvent;
        promptEvent = null;
        showHelp(false);
        try {
            await availablePrompt.prompt();
        } catch {
            showHelp(true);
        }
    });

    button.hidden = false;
})();
