"use strict";
window.SIGDAAgents = (() => {
    const opened = SIGDADatabase.then(db => new Promise((resolve, reject) => {
        const transaction = db.transaction("agents", "readwrite");
        const store = transaction.objectStore("agents");
        const count = store.count();
        count.onsuccess = () => { if (!count.result) for (const [id, agent] of Object.entries(agents)) store.put({ id, ...agent, registration_key: agent.registration.toUpperCase() }); };
        transaction.oncomplete = () => resolve(db); transaction.onerror = reject;
    }));
    async function list() {
        const db = await opened;
        return new Promise((resolve, reject) => {
            const request = db.transaction("agents").objectStore("agents").getAll();
            request.onsuccess = () => resolve(request.result.sort((a,b) => a.name.localeCompare(b.name,"fr")));
            request.onerror = () => reject(new Error("Impossible de lire la base agents."));
        });
    }
    async function save() { throw new Error('La base agents est administrée par l’équipe de maintenance. Utilisez Maintenance et assistance.'); }
    return { list, save };
})();

(() => {
    document.querySelector("[data-new-agent]")?.addEventListener("click", () => { location.hash = "support"; });
    document.querySelector("[data-use-model]")?.addEventListener("click", () => window.dispatchEvent(new CustomEvent("sigda-compose", { detail: { kind: document.getElementById("model").value } })));
    const body = document.querySelector("[data-database-list]");
    if (!body) return;
    const search = document.querySelector("[data-database-search]");
    const status = document.querySelector("[data-database-status]");
    let records = [];
    function show() {
        body.replaceChildren();
        const needle = search.value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
        const selected = records.filter(agent => `${agent.name} ${agent.registration} ${agent.service}`.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().includes(needle));
        for (const agent of selected) {
            const row = document.createElement("tr");
            for (const [index,value] of [agent.name, agent.registration, agent.service].entries()) {
                const cell = document.createElement("td"); cell.dataset.label = ["Nom", "Matricule", "Service"][index]; cell.textContent = value; row.append(cell);
            }
            const cell = document.createElement("td"); cell.dataset.label = "Document"; const link = document.createElement("button");
            link.type = "button"; link.className = "button"; link.textContent = "Créer un document";
            link.addEventListener("click", () => window.dispatchEvent(new CustomEvent("sigda-compose", { detail: { agent: agent.id } })));
            cell.append(link); row.append(cell); body.append(row);
        }
        status.textContent = `${selected.length} dossier(s) affiché(s) dans la base locale.`;
        for (const counter of document.querySelectorAll("[data-agent-count]")) counter.textContent = records.length;
    }
    async function refresh() { try { records = await SIGDAAgents.list(); show(); } catch (error) { status.textContent = error.message; } }
    search.addEventListener("input", show);
    window.addEventListener("sigda-agents-changed", refresh);
    refresh();
})();
