"use strict";

(() => {
    const key = "sigda-demo-session";
    const form = document.getElementById("demo-login");
    const workspace = document.getElementById("demo-workspace");

    function signedIn() {
        try {
            return sessionStorage.getItem(key) === "active";
        } catch {
            return false;
        }
    }

    function showSessionPage() {
        const active = signedIn();
        if (form && active) {
            window.location.replace("./");
        } else if (workspace) {
            workspace.hidden = !active;
            if (!active) window.location.replace("./login.html");
        }
    }

    if (form) {
        const username = document.getElementById("username");
        const password = document.getElementById("password");
        const error = document.getElementById("login-error");
        const submit = document.getElementById("login-submit");

        function showError(message) {
            error.textContent = message;
            error.hidden = false;
        }

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            if (username.value.trim() !== "demo" || password.value !== "SIGDA-demo-2026!") {
                showError("Identifiant ou mot de passe de démonstration incorrect.");
                password.select();
                return;
            }
            try {
                sessionStorage.setItem(key, "active");
            } catch {
                showError("Autorisez le stockage de session du navigateur pour ouvrir la démonstration.");
                return;
            }
            window.location.replace("./");
        });
        submit.disabled = false;
    } else if (workspace) {
        document.getElementById("demo-logout").addEventListener("click", () => {
            sessionStorage.removeItem(key);
            showSessionPage();
        });
    }

    showSessionPage();
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) showSessionPage();
    });
})();
