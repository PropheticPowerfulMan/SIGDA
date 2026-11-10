"use strict";

(() => {
    const storageKey = "sigda-demo-requests";
    const form = document.getElementById("demo-request-form");
    const agentSelect = document.getElementById("request-agent");
    const modelSelect = document.getElementById("request-model");
    const list = document.getElementById("demo-request-list");
    const journal = document.getElementById("demo-activity-log");
    const status = document.getElementById("demo-request-status");
    const labels = {
        draft: "Brouillon",
        submitted: "En attente de décision",
        approved: "Approuvée",
        rejected: "Refusée",
    };
    const formatter = new Intl.DateTimeFormat("fr", { dateStyle: "short", timeStyle: "short" });
    const percent = new Intl.NumberFormat("fr", { style: "percent", maximumFractionDigits: 1 });
    let requests = [];
    try {
        const saved = JSON.parse(sessionStorage.getItem(storageKey));
        if (Array.isArray(saved)) requests = saved;
    } catch {
        // Les actions restent disponibles pour la page en cours.
    }

    function element(tag, text, className = "") {
        const result = document.createElement(tag);
        result.textContent = text;
        result.className = className;
        return result;
    }

    function addAction(request, next, note = "") {
        request.events.push({ status: next, at: Date.now(), note });
        try {
            sessionStorage.setItem(storageKey, JSON.stringify(requests));
        } catch {
            // Le journal reste disponible jusqu’au prochain rechargement.
        }
        render();
        status.textContent = labels[next];
    }

    function addButton(container, text, action, primary = false) {
        const button = element("button", text, primary ? "button button-primary" : "button");
        button.type = "button";
        button.addEventListener("click", action);
        container.append(button);
    }

    function renderRequest(request, index) {
        const row = document.createElement("li");
        const current = request.events.at(-1).status;
        row.append(
            element("strong", documents[request.model].title),
            element("p", agents[request.agent].name, "demo-muted"),
            element("span", labels[current], "status-pill"),
        );
        const actions = element("div", "", "view-actions");
        if (current === "draft") {
            addButton(actions, "Soumettre", () => addAction(request, "submitted"), true);
        } else if (current === "submitted") {
            const note = document.createElement("input");
            note.id = `demo-note-${index}`;
            note.maxLength = 500;
            note.placeholder = "Motif du refus";
            const label = element("label", "Motif du refus", "sr-only");
            label.htmlFor = note.id;
            actions.append(label, note);
            addButton(actions, "Simuler l’approbation", () => addAction(request, "approved"), true);
            addButton(actions, "Simuler le refus", () => {
                if (note.value.trim()) {
                    addAction(request, "rejected", note.value.trim());
                } else {
                    status.textContent = "Indiquez le motif du refus.";
                    note.focus();
                }
            });
        }
        row.append(actions);
        return row;
    }

    function render() {
        list.replaceChildren(...requests.map(renderRequest).reverse());
        if (!requests.length) list.append(element("li", "Aucune demande dans cet onglet."));
        const events = requests.flatMap((request) => request.events.map((event) => ({ request, ...event })));
        const submitted = events.filter((event) => event.status === "submitted").length;
        const pending = requests.filter((request) => request.events.at(-1).status === "submitted").length;
        const approved = events.filter((event) => event.status === "approved").length;
        const refused = events.filter((event) => event.status === "rejected").length;
        document.getElementById("demo-count-submitted").textContent = submitted;
        document.getElementById("demo-count-pending").textContent = pending;
        document.getElementById("demo-approval-rate").textContent = approved + refused ? percent.format(approved / (approved + refused)) : "—";
        document.getElementById("demo-decision-count").textContent = `${approved + refused} décision(s)`;
        journal.replaceChildren();
        for (const event of events.reverse().sort((left, right) => right.at - left.at)) {
            const row = document.createElement("li");
            row.append(
                element("strong", labels[event.status]),
                element("p", `${agents[event.request.agent].name} · ${documents[event.request.model].title}`),
                element("p", formatter.format(event.at), "demo-muted"),
            );
            if (event.note) row.append(element("p", event.note));
            journal.append(row);
        }
        if (!events.length) journal.append(element("li", "Le journal se remplit à mesure que vous traitez des demandes."));
    }

    for (const [key, agent] of Object.entries(agents)) agentSelect.add(new Option(agent.name, key));
    for (const [key, document] of Object.entries(documents)) modelSelect.add(new Option(document.title, key));
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const request = { agent: agentSelect.value, model: modelSelect.value, events: [] };
        if (!Object.hasOwn(agents, request.agent) || !Object.hasOwn(documents, request.model)) return;
        requests.push(request);
        addAction(request, "draft");
    });
    render();
})();
