"use strict";

(() => {
    const key = "sigda-demo-session";
    const entryKey = "sigda-demo-entry";
    const revision = new URL(document.currentScript.src).searchParams.get("v");
    const form = document.getElementById("demo-login");
    const workspace = document.getElementById("demo-workspace");
    const usernames = { demo: "OPS", ops: "OPS", secad: "SECAD", ap: "AP", dircab: "DIRCAB" };
    try { window.SIGDASession = { role: sessionStorage.getItem("sigda-demo-role"), username: sessionStorage.getItem("sigda-demo-user") }; } catch { window.SIGDASession = {}; }

    function signedIn() {
        try {
            return sessionStorage.getItem(key) === "active";
        } catch {
            return false;
        }
    }

    function showSessionPage() {
        const active = signedIn();
        if (workspace) {
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

        for (const profile of document.querySelectorAll("[data-demo-profile]")) profile.addEventListener("click", () => {
            username.value = profile.dataset.demoProfile; password.value = "SIGDA-demo-2026!"; submit.focus();
        });
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const role = usernames[username.value.trim().toLowerCase()];
            if (!role || password.value !== "SIGDA-demo-2026!") {
                showError("Identifiant ou mot de passe de démonstration incorrect.");
                password.select();
                return;
            }
            try {
                sessionStorage.setItem(key, "active");
                sessionStorage.setItem(entryKey, "yes");
                sessionStorage.setItem("sigda-demo-role", role);
                sessionStorage.setItem("sigda-demo-user", role.toLowerCase());
            } catch {
                showError("Autorisez le stockage de session du navigateur pour ouvrir la démonstration.");
                return;
            }
            await window.SIGDAUsage?.log("login");
            navigate("./", window.location.hash);
        });
        submit.disabled = false;
    } else if (workspace) {
        async function logout() {
            await window.SIGDAUsage?.log("logout");
            sessionStorage.removeItem(key);
            sessionStorage.removeItem(entryKey);
            sessionStorage.removeItem("sigda-demo-role"); sessionStorage.removeItem("sigda-demo-user");
            workspace.hidden = true;
            navigate("./login.html");
        }
        for (const button of workspace.querySelectorAll("[data-logout]")) {
            button.addEventListener("click", logout);
        }
    }

    if (workspace) {
        let entry = false;
        try { entry = sessionStorage.getItem(entryKey) === "yes"; sessionStorage.removeItem(entryKey); } catch {}
        if (!entry) { workspace.hidden = true; navigate("./login.html", window.location.hash); }
        else showSessionPage();
    }
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) showSessionPage();
    });
})();
