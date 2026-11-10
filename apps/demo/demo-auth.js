"use strict";

(() => {
    const key = "sigda-demo-session";
    const revision = new URL(document.currentScript.src).searchParams.get("v");
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
            navigate("./", window.location.hash);
        } else if (workspace) {
            workspace.hidden = !active;
            if (!active) navigate("./login.html", window.location.hash);
        }
    }

    function navigate(path, hash = "") {
        const target = new URL(path, window.location.href);
        if (revision) target.searchParams.set("v", revision);
        target.hash = hash;
        window.location.replace(target.href);
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
            navigate("./", window.location.hash);
        });
        submit.disabled = false;
    } else if (workspace) {
        document.getElementById("demo-logout").addEventListener("click", () => {
            sessionStorage.removeItem(key);
            workspace.hidden = true;
            navigate("./login.html");
        });
    }

    showSessionPage();
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) showSessionPage();
    });
})();
